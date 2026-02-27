import asyncio
from asyncua import Client, Node, ua
from asyncua.common.events import Event
from common.helper import make_nodeid_string
from ua_job_aas import create_aas_for_job

from config import (
    UA_ENDPOINT_URL,
    UA_REQUEST_TIMEOUT,
    UA_MACHINE_INSTANCE_NODEID,
    UA_PUBLISHING_INTERVAL
)

EVENT_QUEUE: asyncio.Queue[Event] = asyncio.Queue(100)
EVENT_TYPE_NODEID: str | None = None

class SubscriptionHandler:
    """
    The SubscriptionHandler is used to handle the data that is received for the subscription.
    """

    async def event_notification(self, event: Event):
        """
        Callback for asyncua Subscription.
        This method will be called when the Client received an event message from the Server.
        """
        await EVENT_QUEUE.put(event)


async def process_event(eventtype_nodeid: str | None = None):
    event = await EVENT_QUEUE.get()
    if event is None:
        return
    if (event.EventType.to_string() == eventtype_nodeid):
        print("Received ISA95 Job Order Status Event")
        edata = event.get_event_props_as_fields_dict()
        data = {
            # TODO: Extract more information from the event data, e.g. from the JobOrder, JobState and JobResponse properties
            # FIXME: write helper functions to extract values from Variant-Class to JSON-serializable data
            "JobOrder": {
                "JobOrderID": edata["JobOrder"].Value.JobOrderID,
                "Description": edata["JobOrder"].Value.Description[0].Text,
                "WorkmasterId": edata["JobOrder"].Value.WorkMasterID[0].ID,
                "StartTime": f"{edata['JobOrder'].Value.StartTime}",
                "EndTime": f"{edata['JobOrder'].Value.EndTime}",
                "Priority": edata["JobOrder"].Value.Priority,
            },
            "JobState": edata["JobState"].Value[0].StateText.Text,
            "JobStateNumber": edata["JobState"].Value[0].StateNumber
        }
        await create_aas_for_job(job_data=data)
        return
    else:
        print(f"Received other event type, ignoring... EventType: {event.EventType.to_string()}")
        return

async def main():
    client = Client(url=UA_ENDPOINT_URL, timeout=UA_REQUEST_TIMEOUT)
    await client.connect()
    print(f"Connected to OPC UA Server at {UA_ENDPOINT_URL}")

    await client.load_data_type_definitions()
    await client.load_type_definitions()

    namespace_array = await client.get_namespace_array()
    print(f"Namespace Array: {namespace_array}")

    machinery_index = namespace_array.index("http://opcfoundation.org/UA/Machinery/")
    print(f"Found OPC for Machinery namespace with index: {machinery_index}")
    machinery_jobs_index = namespace_array.index("http://opcfoundation.org/UA/Machinery/Jobs/")
    print(f"Found OPC for Machinery Jobs namespace with index: {machinery_jobs_index}")

    machine_nodeid = make_nodeid_string(UA_MACHINE_INSTANCE_NODEID, namespace_array)
    machine_node: Node = client.get_node(machine_nodeid)
    print(f"Found machine instance ({machine_nodeid}): {await machine_node.read_display_name()}")

    # TODO: Extract Machine Identification information from the machine_node and create an AAS for the machine if it does not exist yet

    building_blocks_node: Node = await machine_node.get_child(f"{machinery_index}:MachineryBuildingBlocks")
    print(f"Found OPC for Machinery BuildingBlocks node: {await building_blocks_node.read_display_name()}")

    job_manager_node: Node = await building_blocks_node.get_child(f"{machine_node.nodeid.NamespaceIndex}:JobManager")
    print(f"Found OPC for Machinery JobManager node: {await job_manager_node.read_display_name()}")

    job_order_results_node: Node = await job_manager_node.get_child(f"{machinery_jobs_index}:JobOrderResults")
    print(f"Found OPC for Machinery JobOrderResults node: {await job_order_results_node.read_display_name()}")

    references = await job_order_results_node.get_references(refs=ua.ObjectIds.GeneratesEvent)
    print(f"Found {len(references)} GeneratesEvent references from Machinery JobOrderResults node")
    if len(references) == 0:
        print("No GeneratesEvent reference found for Machinery JobOrderResults node, cannot subscribe to events!")
        return
    ref_des = references[0]
    EVENT_TYPE_NODEID = ref_des.NodeId.to_string()
    found_eventtype_node = client.get_node(EVENT_TYPE_NODEID)
    print(f"Using EventType-NodeId: {EVENT_TYPE_NODEID} -> {await found_eventtype_node.read_display_name()}")

    handler = SubscriptionHandler()
    subscription = await client.create_subscription(
        period=UA_PUBLISHING_INTERVAL,
        handler=handler,
        publishing=True
    )
    await subscription.subscribe_events(
        sourcenode=job_order_results_node,
        evtypes=[
            found_eventtype_node,
        ],
        where_clause_generation=True
    )
    while True:
        if EVENT_QUEUE.qsize() > 0:
            await process_event(EVENT_TYPE_NODEID)
        else:
            await asyncio.sleep(UA_PUBLISHING_INTERVAL / 1000)  # Sleep for the publishing interval


if __name__ == "__main__":
    asyncio.run(main())