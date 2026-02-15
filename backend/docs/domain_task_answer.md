## Answer

Response from backend to frontend after payload has been sent

    {

        domain: string      // URL domain to check
        status: string      // Current status of the domain task
        slot_id: int        // ID of the thread-slot dedicated to the associated domain task. -1 on error
        error: string       // Error message. Empty if no error occured

        verbose_output: string[] // Continuous output provided by CSAF Checker in verbose mode
        results_checker: json    // Results of CSAF Checker
    }

Status can be one of the following:
- UNDEFINED:         No status has been set for some reason or another. Default value and likely caused by an error
- INITIALIZED:       Slot has been assigned successfully, but domain task hasn't started yet
- ERROR:             Domain task couldn't be started or ended early because of some error (see error field)
- RUNNING_CHECKER:   Domain task is running CSAF Checker
- DONE_CHECKER:      CSAF Checker is done
- RUNNING_VALIDATOR: Domain task is running CSAF Validator
- DONE_VALIDATOR:    CSAF Checker is done
- CACHED_CHECKER:    CSAF Checker output has been found for requested domain in database cache. No domain task has been started
- CACHED_VALIDATOR:  CSAF Validator output has been found for requested domain in database cache. Domain task has been paused
- PAUSED:            Domain task is paused
