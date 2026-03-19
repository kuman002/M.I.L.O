import base64
import hashlib
import hmac
import os
import time
from array import array
from abc import ABC, abstractmethod


def _load_env_file(base_dir: str) -> None:
    env_path = os.path.join(base_dir, ".env")
    if not os.path.exists(env_path):
        return

    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        return


class DataVault:
    def __init__(self, key_file: str = None):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        if key_file is None:
            key_file = os.path.join(base_dir, "assets", ".vault_key")
        self.key_file = key_file
        os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
        _load_env_file(base_dir)
        self.key = self._load_or_create_key()

        from cryptography.fernet import Fernet
        self._fernet = Fernet(self.key)

    def _load_or_create_key(self) -> bytes:
        env_key = os.getenv("VAULT_MASTER_KEY", "").strip()
        if env_key:
            return env_key.encode("utf-8")
        if os.path.exists(self.key_file):
            with open(self.key_file, "rb") as f:
                return f.read()

        key = self._generate_key()
        with open(self.key_file, "wb") as f:
            f.write(key)
        return key

    def _generate_key(self) -> bytes:
        from cryptography.fernet import Fernet
        return Fernet.generate_key()

    def encrypt(self, plain_text: str) -> str:
        return self._fernet.encrypt(plain_text.encode("utf-8")).decode("utf-8")

    def decrypt(self, cipher_text: str) -> str:
        return self._fernet.decrypt(cipher_text.encode("utf-8")).decode("utf-8")


class PinManager:
    def __init__(self, pin_file: str = None, salt_file: str = None):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        if pin_file is None:
            pin_file = os.path.join(base_dir, "assets", ".pin_hash")
        if salt_file is None:
            salt_file = os.path.join(base_dir, "assets", ".pin_salt")
        self.pin_file = pin_file
        self.salt_file = salt_file
        os.makedirs(os.path.dirname(self.pin_file), exist_ok=True)

    def has_pin(self) -> bool:
        return os.path.exists(self.pin_file) and os.path.exists(self.salt_file)

    def set_pin(self, pin: str) -> None:
        salt = os.urandom(16)
        pin_hash = self._hash_pin(pin, salt)
        with open(self.salt_file, "wb") as f:
            f.write(base64.b64encode(salt))
        with open(self.pin_file, "wb") as f:
            f.write(base64.b64encode(pin_hash))

    def verify_pin(self, pin: str) -> bool:
        try:
            with open(self.salt_file, "rb") as f:
                salt = base64.b64decode(f.read())
            with open(self.pin_file, "rb") as f:
                stored_hash = base64.b64decode(f.read())
        except OSError:
            return False

        current_hash = self._hash_pin(pin, salt)
        return hmac.compare_digest(stored_hash, current_hash)

    def _hash_pin(self, pin: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, 200_000)


def capture_intruder(output_dir: str = None) -> str:
    try:
        import cv2
    except Exception:
        return ""

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if output_dir is None:
        output_dir = os.path.join(base_dir, "assets", ".intruder")
    os.makedirs(output_dir, exist_ok=True)

    cam = None
    result, image = False, None
    try:
        if os.name == "nt" and hasattr(cv2, "CAP_DSHOW"):
            cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        else:
            cam = cv2.VideoCapture(0)

        if not cam or not cam.isOpened():
            return ""

        try:
            cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass

        for _ in range(6):
            result, image = cam.read()
            if result:
                break
            time.sleep(0.03)
    finally:
        if cam is not None:
            cam.release()

    if not result:
        return ""

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filepath = os.path.join(output_dir, f"intruder_{timestamp}.jpg")
    cv2.imwrite(filepath, image)
    return filepath


class BaseSpeakerVerifier(ABC):
    """Abstract interface for speaker verification providers."""

    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
        self.sample_rate = None
        self.frame_length = None

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_unavailable_reason(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def has_profile(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def verify_audio_bytes(self, pcm_bytes: bytes):
        raise NotImplementedError

    @abstractmethod
    def enroll_audio_bytes(self, pcm_bytes: bytes, include_feedback: bool = False):
        raise NotImplementedError


class EagleSpeakerVerifier(BaseSpeakerVerifier):
    def __init__(self, profile_path: str = None, access_key: str = None, threshold: float = 0.7):
        super().__init__(threshold=threshold)
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        _load_env_file(base_dir)
        if profile_path is None:
            profile_path = os.path.join(base_dir, "assets", ".eagle_profile")
        self.profile_path = profile_path
        self._init_error = ""
        self._access_key = access_key or self._resolve_access_key()
        self._pveagle = None
        self._eagle = None
        self._profiler = None

        if not self._access_key:
            self._init_error = "Missing Picovoice access key in .env (PICOVOICE_ACCESS_KEY)."
            return

        try:
            import pveagle
        except Exception as e:
            self._init_error = f"Missing dependency: pveagle ({e})"
            return

        try:
            self._pveagle = pveagle
            profile = self._load_profile()
            # Backward + forward compatibility with different pveagle versions
            if hasattr(pveagle, "create_recognizer"):
                speaker_profile = None
                if profile:
                    try:
                        speaker_profile = pveagle.EagleProfile.from_bytes(profile)
                    except Exception:
                        speaker_profile = None

                if speaker_profile is not None:
                    self._eagle = pveagle.create_recognizer(
                        access_key=self._access_key,
                        speaker_profiles=[speaker_profile],
                    )
                else:
                    self._eagle = None

                self._profiler = pveagle.create_profiler(access_key=self._access_key)
            else:
                # Older API
                self._eagle = pveagle.create(access_key=self._access_key, speaker_profile=profile)
                self._profiler = pveagle.EagleProfiler(access_key=self._access_key)

            if self._eagle is not None:
                self.sample_rate = self._eagle.sample_rate
                self.frame_length = self._eagle.frame_length
            else:
                self.sample_rate = getattr(self._profiler, "sample_rate", 16000)
                self.frame_length = getattr(self._profiler, "frame_length", 512)
        except Exception as e:
            self._init_error = f"Failed to initialize Picovoice Eagle: {e}"
            self._pveagle = None
            self._eagle = None
            self._profiler = None
            self.sample_rate = None
            self.frame_length = None

    def _resolve_access_key(self) -> str:
        key_candidates = [
            "PICOVOICE_ACCESS_KEY",
            "PICOVOICE_API_KEY",
            "PV_ACCESS_KEY",
        ]
        for key_name in key_candidates:
            value = os.getenv(key_name, "").strip().strip('"').strip("'")
            if value:
                return value
        return ""

    def is_available(self) -> bool:
        return self._profiler is not None and self.sample_rate is not None and self.frame_length is not None

    def get_unavailable_reason(self) -> str:
        return self._init_error or "Voice biometrics is unavailable."

    def _load_profile(self):
        if not os.path.exists(self.profile_path):
            return None
        try:
            with open(self.profile_path, "rb") as f:
                return f.read()
        except OSError:
            return None

    def has_profile(self) -> bool:
        return os.path.exists(self.profile_path)

    def verify_audio_bytes(self, pcm_bytes: bytes) -> float:
        if not self.is_available() or not self.has_profile() or not pcm_bytes:
            return None

        if self._eagle is None:
            # lazily create recognizer from saved profile if profiler exists
            try:
                profile_bytes = self._load_profile()
                if not profile_bytes:
                    return None
                if hasattr(self._pveagle, "create_recognizer"):
                    profile_obj = self._pveagle.EagleProfile.from_bytes(profile_bytes)
                    self._eagle = self._pveagle.create_recognizer(
                        access_key=self._access_key,
                        speaker_profiles=[profile_obj],
                    )
                    self.sample_rate = self._eagle.sample_rate
                    self.frame_length = self._eagle.frame_length
                else:
                    self._eagle = self._pveagle.create(access_key=self._access_key, speaker_profile=profile_bytes)
                    self.sample_rate = self._eagle.sample_rate
                    self.frame_length = self._eagle.frame_length
            except Exception:
                return None

        scores = []
        for frame in self._iter_frames(pcm_bytes):
            out = self._eagle.process(frame)
            if isinstance(out, (list, tuple)):
                if out:
                    scores.append(float(out[0]))
            else:
                scores.append(float(out))

        if not scores:
            return None

        return sum(scores) / len(scores)

    def enroll_audio_bytes(self, pcm_bytes: bytes, include_feedback: bool = False):
        if not self.is_available() or not pcm_bytes:
            return (None, "") if include_feedback else None

        percent = 0.0
        last_feedback = ""
        for frame in self._iter_frames(pcm_bytes):
            enroll_result = self._profiler.enroll(frame)
            if isinstance(enroll_result, tuple):
                percent = float(enroll_result[0])
                if len(enroll_result) > 1 and enroll_result[1] is not None:
                    feedback_obj = enroll_result[1]
                    last_feedback = getattr(feedback_obj, "name", str(feedback_obj))
            else:
                percent = float(enroll_result)

            # Different Eagle versions can report progress in either 0..1 or 0..100.
            if 0.0 <= percent <= 1.0:
                percent *= 100.0

            if percent < 0.0:
                percent = 0.0
            elif percent > 100.0:
                percent = 100.0

            if percent >= 100:
                profile = self._profiler.export()
                if hasattr(profile, "to_bytes"):
                    profile_bytes = profile.to_bytes()
                else:
                    profile_bytes = profile

                os.makedirs(os.path.dirname(self.profile_path), exist_ok=True)
                with open(self.profile_path, "wb") as f:
                    f.write(profile_bytes)

                if self._eagle is not None and hasattr(self._eagle, "delete"):
                    self._eagle.delete()

                if hasattr(self._pveagle, "create_recognizer"):
                    profile_obj = self._pveagle.EagleProfile.from_bytes(profile_bytes)
                    self._eagle = self._pveagle.create_recognizer(
                        access_key=self._access_key,
                        speaker_profiles=[profile_obj],
                    )
                else:
                    self._eagle = self._pveagle.create(access_key=self._access_key, speaker_profile=profile_bytes)

                self.sample_rate = self._eagle.sample_rate
                self.frame_length = self._eagle.frame_length
                return (percent, last_feedback) if include_feedback else percent

            return (percent, last_feedback) if include_feedback else percent

    def _iter_frames(self, pcm_bytes: bytes):
        samples = array("h")
        samples.frombytes(pcm_bytes)
        frame_length = self.frame_length or 0
        if frame_length <= 0:
            return

        total = len(samples) - (len(samples) % frame_length)
        for offset in range(0, total, frame_length):
            frame = samples[offset:offset + frame_length]
            yield frame


class VoiceBiometrics(EagleSpeakerVerifier):
    """Backward-compatible alias for the previous biometrics class name."""
    pass
