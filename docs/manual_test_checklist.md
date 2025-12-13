# Manual Exploratory Test Checklist

## Authentication & Security
- Register a new user (valid password) and confirm login works.
- Attempt login with wrong password 5x; confirm account locks and message says "locked for 30 minutes".
- Wait 30 minutes (or modify `ACCOUNT_LOCK_TIMEOUT_MINUTES` in code to 1 for testing) and confirm account auto-unlocks.
- As admin, manually unlock a locked account from Admin Panel; confirm user can login immediately.
- Change password from Settings; ensure old password rejected afterward.
- Verify admin-only pages (Activity, Audit Logs) are inaccessible to non-admin users.

## Onboarding
- Complete onboarding flow with sleep/wake inputs; ensure time budget reflects entries.
- Restart app and confirm onboarding is skipped once completed.

## Task Lifecycle (Functional)
- Create a task with required fields; verify it appears on Dashboard and Tasks list.
- Edit task status to In Progress and Completed; confirm status persists after reload.
- Soft delete a task; confirm it disappears from active list and can be restored/verified in DB.

## Time Logging
- Log hours against a task; confirm totals update in Dashboard summary.
- Log hours without a task (generic category) and verify analytics reflect the entry.

## Analytics
- Review 30-day activity chart; confirm values change after adding/completing tasks.
- Check procrastination/estimation metrics update after logging actual times.

## File/Attachment Handling (if enabled)
- Upload a small image (jpg/png); verify preview and size limits.
- Attempt to upload >5MB file; expect rejection message.

## UI/Navigation
- Confirm navbar routes: Dashboard, Tasks, Log Hours, Analytics, Settings, Admin (for admin), Activity, Audit Logs.

## Performance/Resilience
- Run app in web mode; refresh browser; confirm session handling behaves as expected.
- Simulate offline/slow network (if possible) and check error handling for data operations.
