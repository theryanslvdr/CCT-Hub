# CrossCurrent Hub - Admin FAQs & Troubleshooting
**Last Updated: March 2026**

---

## Table of Contents
1. [Member Management FAQs](#member-management-faqs)
2. [License Management FAQs](#license-management-faqs)
3. [Rewards System FAQs](#rewards-system-faqs)
4. [Transaction FAQs](#transaction-faqs)
5. [Platform Settings FAQs](#platform-settings-faqs)
6. [Troubleshooting Guide](#troubleshooting-guide)
7. [Emergency Procedures](#emergency-procedures)

---

## Member Management FAQs

### Q: How do I create a new member account?
**A:** 
1. Go to Admin Section → Members
2. Click "Add Member" button (top right)
3. Fill in:
   - Full Name
   - Email Address
   - Temporary Password
   - Role (Member, Basic Admin, Super Admin)
4. Enable "Force password change on first login"
5. Click "Create Member"

### Q: How do I change a member's role?
**A:**
1. Go to Admin Section → Members
2. Find the member (use search)
3. Click the pencil (edit) icon
4. Select new role from dropdown
5. Click "Save Changes"

**Note:** Only Master Admin can create/modify Super Admin roles.

### Q: How do I reset a member's password?
**A:** Two methods:

**Method 1: Set Temporary Password**
1. Find member → Click key icon
2. Enter temporary password
3. Enable "Force change on login"
4. Click "Set Password"

**Method 2: Send Reset Email**
1. Find member → Click key icon
2. Click "Send Reset Link"
3. Member receives email with reset link (valid 1 hour)

### Q: Can I delete a member account?
**A:** Yes, with restrictions:
- Click trash icon on member row
- Confirm deletion
- **Cannot delete:** Master Admin account
- **Warning:** This permanently removes all user data

### Q: How do I deactivate a member without deleting?
**A:**
1. Edit member (pencil icon)
2. Change Status to "Inactive"
3. Save changes

Inactive members cannot log in but data is preserved.

### Q: Why can't I see certain admin features?
**A:** Access depends on your role:
- **Basic Admin:** Members, Trading Signals, Team Analytics only
- **Super Admin:** Above + Transactions, Rewards Admin
- **Master Admin:** All features

---

## License Management FAQs

### Q: What's the difference between license types?
**A:**

| Type | Description | Family Support | Compounding |
|------|-------------|----------------|-------------|
| Honorary | Passive investment, grows with master trades | No | Yes (quarterly) |
| Honorary FA | Same as Honorary + family members | Yes (up to 5) | Yes (quarterly) |
| Extended | Fixed value license | No | No |

### Q: How do I create a new license?
**A:**
1. Go to Admin Section → Licenses
2. Click "Add License"
3. Search and select user
4. Choose license type
5. Enter starting amount
6. Set effective start date
7. Click "Create"

### Q: A licensee's value looks wrong. How do I fix it?
**A:** Follow these steps:

1. **Quick Fix:** Click sync icon on license row to force recalculation

2. **Detailed Diagnosis:**
   - Go to Platform Settings → Diagnostics
   - Enter licensee's email
   - Click "Run Diagnostic"
   - Review calculation breakdown

3. **If still wrong:**
   - Verify effective_start_date is correct
   - Check starting_amount matches agreement
   - Run "Batch Sync All" to recalculate all licensees

### Q: How do I add family members to an Honorary FA license?
**A:**
1. Find the Honorary FA license in the table
2. Click the users icon (family management)
3. Click "Add Family Member"
4. Enter:
   - Member name
   - Relationship
   - Starting amount
5. Click "Add"

### Q: How does the quarterly compounding work?
**A:** 
```
LOT Size = truncate(Account Value / 980, 2 decimals)
Daily Profit = LOT Size × 15
```

- LOT size is FIXED for entire quarter
- Recalculated at start of each new quarter
- Only trading days count (excludes weekends + US holidays)
- Master Admin's trades determine daily profit rate

### Q: Why does "Balance Before" show incorrect values?
**A:** Common causes:

1. **Missing withdrawals:** Withdrawals from separate collection may not be included
   - Solution: Check `/api/profit/debug-transactions` for discrepancies

2. **Balance override applied:** Check if adjustment exists
   - Solution: Review balance_overrides in diagnostics

3. **Data sync issue:** 
   - Solution: Force sync the user's license

---

## Rewards System FAQs

### Q: How do I manually award points to a member?
**A:**
1. Go to Rewards Admin
2. Search for the member
3. Click "Credit Points"
4. Enter amount and reason
5. Add a note (required for audit)
6. Click "Credit"

### Q: How do I check a member's points history?
**A:**
1. Go to Rewards Admin
2. Search by email or name
3. View "Points History" section
4. Use filters: All, Earned, Spent, Admin Actions
5. Export to CSV if needed

### Q: What triggers automatic point awards?
**A:**

| Trigger | Points | Automatic |
|---------|--------|-----------|
| Sign Up (verified on first trade) | 25 | Yes |
| First Trade | 25 | Yes |
| First Daily Win | 10 | Yes |
| 5-Day Streak | 50 | Yes (repeatable) |
| 10 Trades Milestone | 125 | Yes |
| Qualified Referral | 150 | Yes |
| Deposit ($50+) | 50 per $50 | Yes |

### Q: How do I run retroactive badge scans?
**A:**
1. Go to Platform Settings → Diagnostics
2. Click "Scan All Members"
3. Wait for completion
4. Review results showing badges awarded

This scans all members' trade history and awards any earned but unawarded badges.

### Q: A badge isn't showing for a member who should have it. What do I do?
**A:**
1. Go to Rewards Admin
2. Look up the member
3. Check their stats match badge requirements
4. If yes, run retroactive scan for that user
5. If still missing, check badge is enabled in Badge Management

### Q: How do streak freezes work?
**A:**
- Members purchase freezes with points (Trade: 200pts, Habit: 150pts)
- Freezes auto-apply when a day is missed
- Inventory tracked per user
- Admins can view freeze history in user lookup

---

## Transaction FAQs

### Q: How do I approve a pending deposit?
**A:**
1. Go to Admin Section → Transactions
2. Filter by "Pending Deposits"
3. Review deposit details and proof
4. Click "Approve" or "Reject"
5. Add note if rejecting

### Q: How do I process a withdrawal request?
**A:**
1. Go to Transactions → Pending Withdrawals
2. Verify:
   - Member has sufficient balance
   - Wallet address is valid
   - No suspicious activity
3. Click "Approve" to process
4. System deducts from member's balance

### Q: Can I reverse a transaction?
**A:**
- **Deposits:** Create negative adjustment via Rewards Admin
- **Withdrawals:** Cannot reverse; create new deposit instead
- **Trades:** Can delete/edit trade in Trade History

### Q: How do I export transaction reports?
**A:**
1. Go to Transactions
2. Set desired filters (date, type, status)
3. Click "Export CSV" button
4. File downloads with all filtered transactions

---

## Platform Settings FAQs

### Q: How do I enable maintenance mode?
**A:**
1. Go to Platform Settings → Maintenance Tab
2. Toggle "Maintenance Mode" ON
3. Enter maintenance message
4. Click "Save All Changes"

**Effect:** All non-admin users see maintenance page. Admins can still access platform.

### Q: How do I set up email notifications (Emailit)?
**A:**
1. Create account at emailit.com
2. Get API key from dashboard
3. Go to Platform Settings → API Keys
4. Enter Emailit API Key
5. Click "Test Connection" to verify
6. Save changes

### Q: How do I configure forum image uploads (Publitio)?
**A:**
1. Visit publit.io and create free account
2. Go to Dashboard → Settings → API
3. Copy API Key and API Secret
4. In Hub: Platform Settings → API Keys → Publitio
5. Paste both values
6. Test connection
7. Save changes

**Free tier:** 500MB storage, 2GB bandwidth/month

### Q: Why isn't the custom logo showing?
**A:**
1. Verify image URL is publicly accessible
2. Check URL ends with image extension (.png, .jpg)
3. Ensure no CORS restrictions on image server
4. Clear browser cache after changing

### Q: How do I change the site colors?
**A:**
1. Go to Platform Settings → Branding
2. Use color pickers or enter hex codes:
   - Primary Color: Main brand color
   - Accent Color: Secondary highlights
3. Preview changes
4. Save All Changes

---

## Troubleshooting Guide

### Problem: Licensee value shows $0

**Diagnosis:**
1. Go to Platform Settings → Diagnostics
2. Enter licensee email
3. Run diagnostic

**Common causes & fixes:**
- Missing `effective_start_date` → Edit license, set date
- Missing `starting_amount` → Edit license, set amount
- Inactive license → Activate in license management
- Calculation error → Force sync the user

### Problem: Points not being awarded

**Diagnosis:**
1. Run System Check (Admin → System Check)
2. Review which step fails

**Common fixes:**
- Step 3 fails: Seed badge definitions via diagnostic
- Step 4 fails: Create promotion rule in database
- Step 5 fails: Check API endpoint routing

### Problem: Withdrawal showing as pending but member says it's processed

**Resolution:**
1. Check withdrawal status in Transactions
2. Verify actual blockchain/payment status
3. If paid: Manually mark as complete
4. If not paid: Process the withdrawal

### Problem: Forum images failing to upload

**Diagnosis:**
1. Check Publitio credentials in Platform Settings
2. Test connection
3. Verify member's file is <2MB
4. Check file is JPG/PNG/GIF/WebP

**If credentials correct but still failing:**
- Check Publitio account storage quota
- Verify API hasn't been rate-limited

### Problem: Password reset emails not arriving

**Resolution:**
1. Verify Emailit API key is configured
2. Test connection in Platform Settings
3. Check member's spam folder
4. Try resending after 5 minutes
5. Alternative: Set temporary password manually

### Problem: Monthly table "Balance Before" values are wrong

**Diagnosis:**
Use debug endpoint:
```
GET /api/profit/debug-transactions
```

**Common causes:**
1. **Withdrawals not included:** Check `total_withdrawals_collection` in response
2. **Balance override:** Check `override_amount` in response
3. **Missing transactions:** Compare `deposits` array with expected

**Fix:** Report findings to development team with debug output

### Problem: Real-time updates not working

**Resolution:**
1. Check WebSocket connection (browser dev tools → Network → WS)
2. Refresh page
3. If persistent: Restart backend service

---

## Emergency Procedures

### Member locked out of account

**Immediate actions:**
1. Go to Admin → Members
2. Find member
3. Reset password with temporary
4. Provide to member securely
5. Ensure "force change" is enabled

### Incorrect mass point deduction

**Recovery steps:**
1. Identify affected users
2. Calculate correct amounts
3. Use Rewards Admin to credit points back
4. Document in audit trail
5. Notify affected members

### Platform showing maintenance to everyone

**If unintended:**
1. Go to Platform Settings → Maintenance
2. Toggle OFF
3. Save changes
4. Verify platform accessible

### Database connection issues

**Signs:**
- System Check shows Step 1 failing
- Pages not loading
- Error messages about database

**Actions:**
1. Check backend logs: `tail -f /var/log/supervisor/backend.err.log`
2. Verify MongoDB connection string
3. Contact hosting provider if persistent

### Complete system outage

**Escalation:**
1. Check backend status: `sudo supervisorctl status`
2. Restart if needed: `sudo supervisorctl restart backend`
3. Check frontend: `sudo supervisorctl restart frontend`
4. Review error logs for root cause
5. Contact development team with logs

---

## Contact Information

### For Technical Issues
- Review error logs
- Run System Check
- Document reproduction steps
- Contact development team

### For Business Issues
- Member complaints → Review transaction history
- License disputes → Run diagnostic, verify agreement terms
- Refund requests → Follow company policy

---

*Document Version: 1.0*
*Last Updated: March 2026*
