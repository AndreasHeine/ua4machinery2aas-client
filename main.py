import asyncio
from asyncua import Client, Node, ua
from ua_job_aas import create_aas_for_job

from config import (
    UA_ENDPOINT_URL,
    UA_REQUEST_TIMEOUT,
    UA_MACHINE_INSTANCE_NODEID,
    UA_PUBLISHING_INTERVAL
)

EVENT_QUEUE: asyncio.Queue = asyncio.Queue(100)
EVENT_TYPE_NODEID: str | None = None

class SubscriptionHandler:
    """
    The SubscriptionHandler is used to handle the data that is received for the subscription.
    """

    async def event_notification(self, event):
        """
        Callback for asyncua Subscription.
        This method will be called when the Client received an event message from the Server.
        """
        await EVENT_QUEUE.put(event)


async def process_event(eventtype_nodeid: str | None = None):
    event = await EVENT_QUEUE.get()
    # print(f"Processing event: {event}")
    if event is None:
        return
    if (event.EventType.to_string() == eventtype_nodeid):
        print("Received ISA95 Job Order Status Event")
        print(event)
        data = {
            # TODO: Map the relevant data from the event to the AAS Job data structure
        }
        print("Creating AAS for Job with data:", data)
        await create_aas_for_job(job_data=data)
        return
    else:
        print(f"Received other event type, ignoring... EventType: {event.EventType.to_string()}")
        return

async def main():
    client = Client(url=UA_ENDPOINT_URL, timeout=UA_REQUEST_TIMEOUT)
    await client.connect()
    print(f"Connected to OPC UA Server at {UA_ENDPOINT_URL}")

    machinery_index = await client.get_namespace_index("http://opcfoundation.org/UA/Machinery/")
    print(f"Found Machinery namespace with index: {machinery_index}")
    machinery_jobs_index = await client.get_namespace_index("http://opcfoundation.org/UA/Machinery/Jobs/")
    print(f"Found Machinery/Jobs namespace with index: {machinery_jobs_index}")

    machine_node: Node = client.get_node(UA_MACHINE_INSTANCE_NODEID)
    print(f"Found machine instance: {await machine_node.read_display_name()}")

    # TODO: Extract Machine Identification information from the machine_node and create an AAS for the machine if it does not exist yet

    building_blocks_node: Node = await machine_node.get_child(f"{machinery_index}:MachineryBuildingBlocks")
    print(f"Found BuildingBlocks node: {await building_blocks_node.read_display_name()}")

    job_manager_node: Node = await building_blocks_node.get_child(f"{machine_node.nodeid.NamespaceIndex}:JobManager")
    print(f"Found JobManager node: {await job_manager_node.read_display_name()}")

    job_order_results_node: Node = await job_manager_node.get_child(f"{machinery_jobs_index}:JobOrderResults")
    print(f"Found JobOrderResults node: {await job_order_results_node.read_display_name()}")

    references = await job_order_results_node.get_references(refs=ua.ObjectIds.GeneratesEvent)
    print(f"Found {len(references)} GeneratesEvent references from JobOrderResults node", references)
    if len(references) == 0:
        print("No GeneratesEvent reference found for JobOrderResults node, cannot subscribe to events!")
        return
    ref_des = references[0]
    EVENT_TYPE_NODEID = ref_des.NodeId.to_string()
    eventtype_node = client.get_node(EVENT_TYPE_NODEID)
    print(f"Using EventType-NodeId: {EVENT_TYPE_NODEID} -> {await eventtype_node.read_display_name()}")

    handler = SubscriptionHandler()
    subscription = await client.create_subscription(
        period=UA_PUBLISHING_INTERVAL,
        handler=handler,
        publishing=True
    )
    await subscription.subscribe_events()  # FIXME: Subscribe only to events of type EVENT_TYPE_NODEID
    while True:
        if EVENT_QUEUE.qsize() > 0:
            await process_event(EVENT_TYPE_NODEID)
        else:
            await asyncio.sleep(UA_PUBLISHING_INTERVAL / 1000)  # Sleep for the publishing interval


if __name__ == "__main__":
    asyncio.run(main())