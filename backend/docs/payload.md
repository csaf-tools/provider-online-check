## Payload

Send from frontend to backend

{
// Required
    domain: string;      // URL domain to check
    session_id: string;  // Unique client session id (like UUID to identify client)

// Optional
    ignore_cache: bool;  // Client wants to check a domain, regardless of database cache. Default: False
    interrupt: bool;     // Client interrupts their request, effectively stopping backend. Default: False
    run_validator: bool; // Runs CSAF Validator after CSAF Checker. Default: True
}

Run Validator flag might need to be a separate payload later on