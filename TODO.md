# TODO Living Document

## MVP

- Platform
	- [X] Authentication - Users can login
	- [~] Authorisation - Users only have access to particular projects
	- [X] Account provisioning
	- [X] Creating engagements
	- [~] Interface with Git KB
	- [X] Interface with Twilight (via export functionality?)
	- [X] Dirty bootstrap UI
	- [ ] Configuration file
	- [ ] Logging
	
- Engagement management
	- [X] Creating / Editing / Delete
	- [X] Prompt / Warn on deletion
	- [X] Alter access controls / perms per user

- Engagement
	- [~] Import test cases from repository
	- [X] Import test cases from MitreLayer dump
	- [X] Delete test case
	- [X] Duplicate test case
	
- Test cases
	- [X] General
		- [X] Name
		- [X] Tagging
		- [X] Sigma rules
	- [X] Red
		- [X] Case start / stop
		- [X] Phase
		- [X] Source
		- [X] Target(s)
		- [X] TTP Boilerplate description
		- [X] Execution description
		- [X] Command description
		- [X] Technique number
		- [X] Red tools
		- [X] Evidence
	- [X] Blue
		- [X] Outcome
		- [X] Prevention level
		- [X] Detection level
		- [X] Blue tools
		- [X] Freeform text for SIEM event IDs / links etc.
		- [X] Evidence
	- [X] Target / source / red+blue tool bank / selection modals
		
## "V2 thing"

- [ ] Platform
	- [X] IP whitelisting
	- [ ] Pretty up UI
	- [X] Teams / slack integrations
	
- [ ] Engagement management
	- [X] Renaming
	- [X] Duplicate
	- [X] Delete
	- [X] Import from template
	- [X] Export to template
	- [ ] Start / end engagement overall timeline

- [ ] Engagement
	- [ ] Attack / escalation path mindmap
	- [ ] Timeline
	
- [ ] Test cases
	- [~] Pull fresh content / sync from git
	- [ ] Push to approval / review queue to update KB
	- [ ] JS lib for image cropping / redacting / highlighting evidence inline
