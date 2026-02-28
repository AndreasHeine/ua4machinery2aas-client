"""Basic smoke test for AAS creation helper entrypoints."""

import asyncio
from datetime import datetime
from common.helper import clean_id
from ua_job_aas import create_aas_for_job
from ua_machine_aas import create_aas_for_identification


async def main():
    """Execute sample test payloads against AAS creation functions."""
    await create_aas_for_job(
        {
            "JobOrder": {
                "JobOrderID": "asdf",
                "Description": "Produce 100 units of product XYZ",
                "WorkmasterId": "WM_001",
                "StartTime": datetime.now().isoformat(),
                "EndTime": datetime.now().isoformat(),
                "Priority": 500,
                "JobOrderParameters": {"JobName": ["XYZ", "xyz"], "OrderNumbers": [100, 101]},
            },
            "JobState": "Ended",
            "JobStateNumber": 5,
        }
    )
    await create_aas_for_identification(
        clean_id("WIWA CoffeeMix"),
        {
            "ProductInstanceUri": "urn:uuid:123e4567-e89b-12d3-a456-426614174000",
            "Manufacturer": "konzeptpark GmbH",
            "Model": "FactoryNexus",
            "SerialNumber": "SN123456789",
        },
    )


if __name__ == "__main__":
    asyncio.run(main())
