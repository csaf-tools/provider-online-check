## Answer

Response from backend to frontend after payload has been sent

{
    domain: string;      // URL domain to check
    status: string;      // Current status of the domain task
    slot_id: int;        // ID of the thread-slot dedicated to the associated domain task. -1 on error
    error: string;       // Error message. Empty if no error occured

    verbose_output: string[] // Continuous output provided by CSAF Checker in verbose mode
    results_checker: string  // Results of CSAF Checker
}

Status can be one of the following:
- Undefined:         No status has been set for some reason or another. Default value and likely caused by an error
- Initialized:       Slot has been assigned successfully, but domain task hasn't started yet
- Error:             Domain task couldn't be started or ended early because of some error (see error field)
- Running_Checker:   Domain task is running CSAF Checker
- Done_Checker:      CSAF Checker is done
- Running_Validator: Domain task is running CSAF Validator
- Done_Validator:    CSAF Checker is done
- Cached_Cache:      CSAF Checker output has been found for requested domain in database cache. No domain task has been started
- Cached_Validator:  CSAF Validator output has been found for requested domain in database cache. Domain task has been paused
- Paused:            Domain task is paused