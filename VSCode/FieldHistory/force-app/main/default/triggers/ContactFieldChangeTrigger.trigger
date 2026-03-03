/**
 * Contact Field Change Trigger
 * Tracks field changes for Contact based on Custom Metadata configuration.
 *
 * Events: after insert, after update
 * (Delete tracking can be added similarly if needed.)
 */
trigger ContactFieldChangeTrigger on Contact (after insert, after update) {
    if (Trigger.isAfter) {
        FieldChangeTrackerHandler.handle(
            'Contact',
            Trigger.new,
            Trigger.oldMap,
            Trigger.isInsert,
            Trigger.isUpdate,
            Trigger.isDelete
        );
    }
}