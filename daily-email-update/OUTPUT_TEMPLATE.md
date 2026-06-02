**Summary**
- New: {{n_new}}  Carryover: {{n_carry}}  Drafts: {{n_drafts}}
- Window: {{start}} → {{end}}  Last checkpoint: {{last_history_id}}
- **Retrieval: {{retrieved_count}}/{{expected_count}} emails processed {{status_icon}}**

{{#if failed_retrievals}}
⚠️ WARNING: {{failed_count}} messages could not be retrieved
{{#each failed_retrievals}}
- Message ID: {{id}} - https://mail.google.com/mail/u/1/#all/{{id}}
{{/each}}
Please review these manually
{{/if}}

## Needs Response
- {{date}} · {{sender}} · {{subject}} — {{one_line}} [open link]

## Needs Action
- {{date}} · {{owner}} · {{action}} — {{one_line}} [open link]

