# 🚀 MILO - Quick Start Guide

## Launch Application

### Option 1: Batch File (Windows)
```bash
launch.bat
```

### Option 2: Command Line
```bash
python src/main.py
```

---

## 📊 Dashboard Tab
**Default view when app opens**

### What You See:
- **Metric Cards** at top showing:
  - 📋 Pending Tasks count
  - 💰 Current Balance
  - 🎯 Active Habits count
- **Upcoming Deadlines** section
- **AI Insights** section
- 🔄 **Refresh Dashboard** button

### Actions:
- View all metrics at a glance
- See upcoming tasks
- Get AI suggestions
- Refresh data manually

---

## ✓ Tasks Tab
**Manage all your tasks**

### How to Add a Task:
1. Click **"✓ Tasks"** tab
2. Enter task title
3. Select priority (LOW/MEDIUM/HIGH)
4. Pick due date (optional)
5. Click **"➕ Add Task"** button

### How to Edit a Task:
1. Find task in the table
2. Click **"✏️"** button on the right
3. Update title/priority in dialog
4. Click **"💾 Save"**

### Table Columns:
- **ID** - Unique task identifier
- **Title** - What the task is
- **Priority** - LOW/MEDIUM/HIGH
- **Due Date** - When it's due
- **Status** - pending/completed
- **Edit** - ✏️ button to modify

### Quick Actions:
- Add new task
- Edit existing task
- Delete task (via delete buttons outside main table)

---

## 💰 Finances Tab
**Track income and expenses**

### How to Add Income:
1. Click **"💰 Finances"** tab
2. Select **"Income"** from Type dropdown
3. Enter amount (e.g., 1500)
4. Select category (salary, freelance, investment, other)
5. Click **"➕ Add"** button

### How to Add Expense:
1. Click **"💰 Finances"** tab
2. Select **"Expense"** from Type dropdown
3. Enter amount (e.g., 50)
4. Select category (Food, Transport, Entertainment, Utilities, Other)
5. Click **"➕ Add"** button

### Table Columns:
- **Type** - Income or Expense
- **Amount** - Dollar amount
- **Category** - Where it's from/going to
- **Date** - When transaction occurred
- **Delete** - 🗑️ button to remove

---

## 🎯 Habits Tab
**Build and track habits**

### How to Add a Habit:
1. Click **"🎯 Habits"** tab
2. Enter habit name (e.g., "Morning Jog")
3. Click **"➕ Add Habit"** button

### How to Log Completion:
1. Find habit in the table
2. Click **"✓ Log"** button
3. Streak counter increases automatically

### Table Columns:
- **Habit** - Name of the habit
- **Streak** - Consecutive completions
- **Log** - ✓ Log button to mark done
- **Delete** - 🗑️ button to remove

---

## 🎤 Voice Commands

### Start Listening:
1. Click **"🎤 Start Listening"** in header
2. Button changes to **"⏹️ Stop Listening"**
3. Status shows **"🎤 Listening..."**
4. Speak your command
5. Button text changes back when done

### Calibrate Microphone:
1. Click **"🎛️ Calibrate"** button
2. Keep quiet for 3 seconds
3. Status updates when calibration complete

### Voice Examples:
- "Add task morning jog high priority"
- "Add expense 50 food"
- "Add habit meditation"
- "Log habit meditation"

---

## 💬 Text Input

### Send Text Command:
1. Type in bottom input field
2. Press **Enter** or click **"📤 Send"**
3. MILO processes command
4. Response appears in message area above
5. MILO speaks the response aloud

### Example Commands:
- "remind me tomorrow at 9am"
- "add task project deadline tomorrow"
- "what is my balance"
- "show me my habits"

---

## ⚙️ Status Indicators

### Header Status (Top Right):
- **✅ Ready** (Green) - Application is idle
- **🎤 Listening...** (Blue) - Voice listening active
- **🎛️ Calibrating...** (Yellow) - Microphone calibration in progress

---

## 🔄 Auto-Features

### Automatic Refresh:
- Dashboard refreshes every 30 seconds
- All data stays up-to-date automatically
- Manual refresh button available on Dashboard

### Voice Feedback:
- All actions produce audio confirmation
- "Task added", "Transaction recorded", etc.
- Powered by text-to-speech

### Message Display:
- All responses shown in footer message area
- Scroll to see full messages
- Cleared when new command sent

---

## 💡 Tips & Tricks

### Quick Actions:
- **Enter Key** - Send text input without clicking button
- **Tab Switch** - Click tab names to switch sections
- **Multiple Inputs** - All inputs can be filled before adding

### Data Management:
- All data saved to database automatically
- Previous sessions load on startup
- Deleted items are permanent (confirm before deleting)

### Viewing Data:
- Tables show most recent items first
- Scroll horizontally for long tables
- Column widths auto-adjust

---

## ⚠️ Troubleshooting

### App won't start?
```bash
# Verify dependencies installed
pip install -r requirements.txt

# Run the app
python src/main.py
```

### Voice not working?
1. Click **"🎛️ Calibrate"** button
2. Ensure microphone is connected
3. Check microphone permissions

### Can't add items?
1. Verify all required fields filled
2. Check for error messages
3. Try refreshing tab

### Data not updating?
1. Click refresh button
2. Switch to another tab and back
3. Restart application

---

## 📋 Summary of Tabs

| Tab | Purpose | Main Action |
|-----|---------|------------|
| 📊 Dashboard | Overview & insights | View metrics, see deadlines |
| ✓ Tasks | Task management | Add, edit, complete tasks |
| 💰 Finances | Money tracking | Log income/expenses |
| 🎯 Habits | Build habits | Add habits, log completions |

---

## 🎯 Next Steps

1. **Try Adding a Task** - Click Tasks tab
2. **Log a Transaction** - Click Finances tab
3. **Create a Habit** - Click Habits tab
4. **Use Voice** - Try voice commands
5. **Explore Dashboard** - See all data together

---

## 📞 Need Help?

All buttons have clear emoji icons showing what they do:
- ➕ = Add new item
- ✏️ = Edit item
- 🗑️ = Delete item
- ✓ = Complete/Confirm action
- 🔄 = Refresh data
- 📤 = Send command
- 🎤 = Voice control

**Hover over buttons or try clicking them to learn what they do!**

---

🎉 **Enjoy using MILO!** 🎉
