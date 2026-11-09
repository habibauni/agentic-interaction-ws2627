# Delegation

| # | Action | Decision | Justification |
|---|--------|----------|---------------|
| 1 | Read the appointments of a day | Alone | Read-only action with no side effects. |
| 2 | Look up the weather | Alone | Provides public, read-only information with no side effects. |
| 3 | Search train connections | Alone | Only retrieves information. Searching does not book or commit to anything. The results are needed to make informed suggestions. |
| 4 | Read notes | Alone | Reading private notes has no external effects. They provide important information missing from the calendar. |
| 5 | Create a personal block in the calendar | Approval | Even though the block only affects my personal calendar and can be deleted, creating it changes my schedule. I should approve the time and details before it is added. |
| 6 | Reschedule an appointment with other attendees | Approval | Affects other people's calendars and sends notifications. Incorrect changes can inconvenience others and cannot be easily reversed. |
| 7 | Book a train ticket | Approval | Involves spending money, possible cancellation fees and personal travel preferences, therefor a booking summary needs approval first. |
| 8 | Send a message to third parties | Approval | Reaches other people, so the draft and recipient needs approval before sending. |
| 9 | Create a note | Approval | Creating a note adds new information to my personal records. I should confirm its content and purpose before it is saved. |
| 10 | Delete a note | Approval | Deletion is irreversible, therefor a confirmation is required. |

## Rule
 Read-only actions can be performed independently. Actions that create, purchase or impact others require a summary and prior approval.

## Observations

1. Unnecessary approval requests can slow down simple tasks: When asked "What's on today?", the agent could read the calendar directly without asking for permission. Requesting approval for  read-only actions would only delay the response without giving the user any additional control.

2. A vague instruction does not always provide enough permission to act: When asked to "tidy up my notes", the agent could not know which notes were outdated or safe to delete. It needed clarification before deleting anything.