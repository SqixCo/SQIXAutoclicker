/**
 * FieldChangeTrackerHandler
 *
 * Generic handler that logs old/new values for configured fields using Custom Metadata.
 *
 * Assumptions:
 * 1) Custom Object: Field_Change_Log__c
 *    Fields used here:
 *      - Object__c (Text)
 *      - Record_Id__c (Text 18)
 *      - Record_Name__c (Text 255) [optional]
 *      - Field__c (Text)
 *      - Old_Value__c (Long Text)
 *      - New_Value__c (Long Text)
 *      - Changed_By__c (Lookup(User)) [optional]
 *      - Changed_On__c (DateTime) [optional]
 *      - Change_Type__c (Picklist: Create, Update, Delete) [optional]
 *      - Transaction_Id__c (Text) [optional]
 *
 * 2) Custom Metadata:
 *    - Field_Tracking_Object__mdt:
 *        Object__c (Text)
 *        IsEnabled__c (Checkbox)
 *        Track_Creates__c (Checkbox)
 *        Track_Updates__c (Checkbox)
 *        Track_Deletes__c (Checkbox) [optional]
 *
 *    - Field_Tracking_Field__mdt:
 *        Object__c (Text)
 *        Field__c (Text)
 *        IsEnabled__c (Checkbox)
 *        Track_On_Create__c (Checkbox)
 *        Track_On_Update__c (Checkbox)
 */
public with sharing class FieldChangeTrackerHandler {

    // Prevent recursion within same transaction.
    private static Boolean isRunning = false;

    public static void handle(
        String objectApiName,
        List<SObject> newList,
        Map<Id, SObject> oldMap,
        Boolean isInsert,
        Boolean isUpdate,
        Boolean isDelete
    ) {
        if (isRunning) return;
        isRunning = true;

        try {
            // Basic safety
            if (String.isBlank(objectApiName) || newList == null || newList.isEmpty()) return;

            // 1) Check if tracking is enabled for this object + event
            Field_Tracking_Object__mdt objCfg = getObjectConfig(objectApiName);
            if (objCfg == null || objCfg.IsEnabled__c == false) return;

            if (isInsert && (objCfg.Track_Creates__c == null || objCfg.Track_Creates__c == false)) return;
            if (isUpdate && (objCfg.Track_Updates__c == null || objCfg.Track_Updates__c == false)) return;
            // If you later add delete, handle it here.

            // 2) Get fields to track for this object
            Set<String> fieldsToTrack = getFieldsToTrack(objectApiName, isInsert, isUpdate);
            if (fieldsToTrack.isEmpty()) return;

            // 3) Validate fields exist on object (prevents runtime errors if CMDT is misconfigured)
            Schema.SObjectType sObjType = Schema.getGlobalDescribe().get(objectApiName);
            if (sObjType == null) return;

            Map<String, Schema.SObjectField> describeFields = sObjType.getDescribe().fields.getMap();

            // 4) Build logs
            List<Field_Change_Log__c> logs = new List<Field_Change_Log__c>();
            String txnId = buildTxnId();

            for (SObject newRec : newList) {
                Id rid = (Id)newRec.get('Id');
                SObject oldRec = (oldMap != null && rid != null) ? oldMap.get(rid) : null;

                // For insert: oldRec will be null
                for (String fieldApi : fieldsToTrack) {
                    if (!describeFields.containsKey(fieldApi)) {
                        // Skip invalid field API names
                        continue;
                    }

                    Object newVal = newRec.get(fieldApi);
                    Object oldVal = (oldRec == null) ? null : oldRec.get(fieldApi);

                    if (isInsert) {
                        // Log only if new value is non-null (optional rule; change if you want all fields)
                        if (newVal == null) continue;

                        logs.add(buildLog(
                            objectApiName, newRec, fieldApi,
                            null, newVal,
                            'Create', txnId
                        ));
                    } else if (isUpdate) {
                        if (!valuesDiffer(oldVal, newVal)) continue;

                        logs.add(buildLog(
                            objectApiName, newRec, fieldApi,
                            oldVal, newVal,
                            'Update', txnId
                        ));
                    }
                }
            }

            // 5) DML (bulk insert)
            if (!logs.isEmpty()) {
                insert logs;
            }

        } finally {
            isRunning = false;
        }
    }

    // -------------------------
    // Custom Metadata fetchers
    // -------------------------

    private static Field_Tracking_Object__mdt getObjectConfig(String objectApiName) {
        // DeveloperName is not guaranteed to match; filter by Object__c
        List<Field_Tracking_Object__mdt> rows = [
            SELECT Object__c, IsEnabled__c, Track_Creates__c, Track_Updates__c, Track_Deletes__c
            FROM Field_Tracking_Object__mdt
            WHERE Object__c = :objectApiName
            LIMIT 1
        ];
        return rows.isEmpty() ? null : rows[0];
    }

    private static Set<String> getFieldsToTrack(String objectApiName, Boolean isInsert, Boolean isUpdate) {
        Set<String> fields = new Set<String>();

        List<Field_Tracking_Field__mdt> rows = [
            SELECT Object__c, Field__c, IsEnabled__c, Track_On_Create__c, Track_On_Update__c
            FROM Field_Tracking_Field__mdt
            WHERE Object__c = :objectApiName
              AND IsEnabled__c = true
        ];

        for (Field_Tracking_Field__mdt r : rows) {
            if (String.isBlank(r.Field__c)) continue;

            if (isInsert && r.Track_On_Create__c == true) fields.add(r.Field__c.trim());
            if (isUpdate && r.Track_On_Update__c == true) fields.add(r.Field__c.trim());
        }

        return fields;
    }

    // -------------------------
    // Log construction helpers
    // -------------------------

    private static Field_Change_Log__c buildLog(
        String objectApiName,
        SObject rec,
        String fieldApiName,
        Object oldVal,
        Object newVal,
        String changeType,
        String txnId
    ) {
        Field_Change_Log__c logRow = new Field_Change_Log__c();
        logRow.Object__c = objectApiName;
        logRow.Record_Id__c = (String)rec.get('Id');

        // Best-effort record name (works for Contact)
        if (rec.getSObjectType() == Contact.SObjectType) {
            logRow.Record_Name__c = (String)rec.get('Name');
        }

        logRow.Field__c = fieldApiName;
        logRow.Old_Value__c = stringifyValue(oldVal);
        logRow.New_Value__c = stringifyValue(newVal);

        // Optional fields if you created them
        try { logRow.Change_Type__c = changeType; } catch (Exception e) {}
        try { logRow.Changed_By__c = UserInfo.getUserId(); } catch (Exception e) {}
        try { logRow.Changed_On__c = System.now(); } catch (Exception e) {}
        try { logRow.Transaction_Id__c = txnId; } catch (Exception e) {}

        return logRow;
    }

    private static String stringifyValue(Object v) {
        if (v == null) return null;

        if (v instanceof Date) {
            return String.valueOf((Date)v);
        }
        if (v instanceof Datetime) {
            // ISO-ish, consistent
            return ((Datetime)v).formatGmt('yyyy-MM-dd\'T\'HH:mm:ss\'Z\'');
        }
        if (v instanceof Boolean) {
            return ((Boolean)v) ? 'true' : 'false';
        }
        if (v instanceof Decimal) {
            return String.valueOf((Decimal)v);
        }
        // Covers Id, String, Integer, etc.
        return String.valueOf(v);
    }

    private static Boolean valuesDiffer(Object oldVal, Object newVal) {
        if (oldVal == null && newVal == null) return false;
        if (oldVal == null || newVal == null) return true;

        // Normalize to String to handle most types consistently
        return stringifyValue(oldVal) != stringifyValue(newVal);
    }

    private static String buildTxnId() {
        // Lightweight unique-ish id per transaction
        // (good enough for grouping logs made in the same execution)
        return String.valueOf(System.now().getTime()) + '-' + String.valueOf(Crypto.getRandomInteger());
    }
}