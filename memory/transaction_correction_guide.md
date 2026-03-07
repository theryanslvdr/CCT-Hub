# Transaction Correction Guide

This guide explains how members and admins can correct transaction amounts in CrossCurrent Hub.

---

## For Members: Self-Edit Your Transactions

### When Can You Edit?
- You can edit your **last 2 deposits or withdrawals** only
- You have a **48-hour window** from when the transaction was created
- If an admin has already corrected a transaction, you cannot edit it further

### Step-by-Step

1. **Go to the Profit Tracker page**
   - Click "Profit Tracker" in the sidebar under CORE

2. **Scroll down to "My Recent Transactions"**
   - At the bottom of the page, you'll see the "My Recent Transactions" section
   - This shows your recent deposits and withdrawals with their amounts and dates

![My Recent Transactions section on the Profit Tracker page](/guide-images/member-my-transactions.png)

3. **Click "Edit" on the transaction you want to correct**
   - Each editable transaction has a blue **Edit** button on the right side
   - You'll also see how much time is left in the 48-hour edit window (e.g., "23h 45m left to edit")
   - If you see a lock icon instead, the 48-hour window has expired and the transaction can no longer be edited

4. **Enter the correct amount**
   - A dialog will appear showing the current amount
   - Type the correct dollar amount in the **Correct Amount ($)** field (just the number, no $ sign needed)
   - Optionally, type a reason for the change in the **Reason** field (e.g., "Entered wrong amount")

5. **Click "Update"**
   - Your balance will update immediately
   - The transaction will show an **"Edited"** badge next to the amount
   - The admin will be notified of the change

### Rules
- Only deposits and withdrawals can be edited (not trades or commissions)
- You can only edit **once** — make sure the amount is correct before confirming
- The 48-hour countdown starts from when the transaction was originally created
- Transactions corrected by an admin are locked and cannot be edited by you

---

## For Admins: Correct Any Member's Transaction

### When Should You Correct?
- When a member reports entering the wrong amount
- When you spot an incorrect deposit or withdrawal during reconciliation
- When a member's 48-hour edit window has expired and they need a fix

### Step-by-Step

1. **Go to Admin > Transactions**
   - Expand the **ADMIN** section in the sidebar
   - Click **"Transactions"** to open the Team Transactions page
   - You'll see summary cards for Total Deposits, Total Withdrawals, Net Flow, and Unique Depositors

![Admin Team Transactions page](/guide-images/admin-transactions.png)

2. **Find the transaction**
   - The **Transaction History** table shows all member transactions
   - Use the **Search** bar to find a specific member by name or email
   - Use the filter tabs (**All**, **Deposits**, **Withdrawals**, **Profits**) to narrow results
   - Each row shows: Type, Member, Amount, Product/Notes, Date, and Actions

3. **Click the pencil (edit) icon**
   - In the **Actions** column on the right side of each transaction row, click the **pencil icon**
   - This opens the **Correct Transaction** dialog
   - Note: Transactions that have already been corrected will show a **"Corrected"** badge

4. **Enter the corrected amount and reason**
   - The dialog shows the member's name, date, and original amount
   - Enter the correct dollar amount in the **New Amount ($)** field
   - Provide a reason in the **Reason for Correction** field (e.g., "Member entered wrong amount")

![Admin Correction Dialog](/guide-images/admin-correction-dialog.png)

5. **Click "Apply Correction"**
   - The member's balance updates **immediately**
   - An audit trail is recorded with:
     - Who made the correction (your name)
     - When it was corrected
     - The original amount vs. new amount
     - The reason provided
   - The transaction will show a **"Corrected"** badge in the list
   - The member will be notified of the change

### Admin Correction Rules
- Admin corrections **lock** the transaction — the member can no longer edit it
- All corrections are logged in the audit trail for full accountability
- There is **no time limit** for admin corrections (unlike the 48-hour member limit)
- You can correct the same transaction multiple times if needed — each correction is logged

---

## Quick Reference

| Feature | Member | Admin |
|---------|--------|-------|
| **Where** | Profit Tracker > My Recent Transactions | Admin > Transactions |
| **What can be edited** | Last 2 deposits/withdrawals | Any deposit/withdrawal |
| **Time limit** | 48 hours | No limit |
| **Edits allowed** | Once per transaction | Unlimited (each logged) |
| **Audit trail** | Yes | Yes |
| **Balance update** | Immediate | Immediate |
| **Locks transaction?** | No | Yes (member can't edit after) |
