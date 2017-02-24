"""
Adding a plan:

    1) Register the plan with Stripe in both test and prod
    2) Add the plan here
    3) Toggle it to active
    4) Ensure that the price here matches Stripe and that the "days" term matches when stripe renews it
    5) Make sure that it is added to the appropriate boss_plan or flex_plan below
    6) Add to frontend plan functions
        * app/static/javascript/shared/app/models/organization.js


Important fields:
    The dict key is the stripe id for the subscription
    "name" is the public-facing plan name
    "description" is the public-facing description
    "unit_price" is the CENTS per time unit
    "term" is how many days each renewal extends the account. May want to add some grace period here. 
    "active" is whether new accounts can select this. Deleting a plan where a user exists can stop extending their service grant.
"""

plans = {
    "per-seat-v1": {
        "name": "Boss",
        "description": "Workers assigned shifts",
        "unit_price": 500,
        "term": "monthly",
        # This is just used in the sign-up form
        "for": "Employees",
        "active": False,
        "paid_labs_id": {
            # env -> id
            "live": "",
            "test": "",
        },
    },
    "flex-v1": {
        "name": "Flex",
        "description": "Workers claim shifts",
        "unit_price": 300,
        "term": "monthly",
        "for": "Contractors",
        "active": False,
    },
    "boss-v2": {
        "name": "Boss",
        "description": "Workers assigned shifts",
        "unit_price": 10000,
        "term": "monthly",
        # This is just used in the sign-up form
        "for": "Employees",
        "active": True,
        "max_workers": 40,
        "paid_labs_id": {
            # env -> id
            "live": "pl_nzqzUFpT5oghUqDSSKDCw",
            "test": "pl_5XCsgVuBEMchRt6zn3pAbQ",
        },
    },
    "flex-v2": {
        "name": "Flex",
        "description": "Workers claim shifts",
        "unit_price": 6000,
        "term": "monthly",
        "for": "Contractors",
        "active": True,
        "max_workers": 40,
        "paid_labs_id": {
            # env -> id
            "live": "pl_9nMxLFxvAUQnXpAXPLZ1fw",
            "test": "pl_553d9YPSxlbAGc67JClSw",
        },
    },
}

term_to_days = {
    "monthly": 32,
}

# plan group
boss_plans = ["per-seat-v1", "boss-v2"]
flex_plans = ["flex-v1", "flex-v2"]
