# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from pypika import CustomFunction


@frappe.whitelist()
def get_app_version():
    return frappe.get_attr("insights" + ".__version__")


@frappe.whitelist()
def get_data_sources():
    return frappe.get_list(
        "Data Source",
        fields=["name", "title", "status", "database_type", "modified", "username"],
    )


@frappe.whitelist()
def get_tables(data_source=None):
    if not data_source:
        return []

    def get_all_tables():
        return frappe.get_all(
            "Table",
            filters={"data_source": data_source},
            fields=["table", "label"],
        )

    return frappe.cache().hget(
        "insights",
        "get_tables_" + data_source,
        generator=get_all_tables,
    )


@frappe.whitelist()
def get_dashboard_list():
    return frappe.get_list(
        "Insights Dashboard",
        fields=["name", "title", "modified"],
    )


@frappe.whitelist()
def create_dashboard(title):
    dashboard = frappe.get_doc(
        {"doctype": "Insights Dashboard", "title": title}
    ).insert()
    return dashboard.name


@frappe.whitelist()
def get_queries():
    frappe.has_permission("Query", throw=True)
    Query = frappe.qb.DocType("Query")
    QueryTable = frappe.qb.DocType("Query Table")
    GroupConcat = CustomFunction("Group_Concat", ["column"])
    return (
        frappe.qb.from_(Query)
        .left_join(QueryTable)
        .on(Query.name == QueryTable.parent)
        .select(
            Query.name,
            Query.title,
            GroupConcat(QueryTable.label).as_("tables"),
            Query.data_source,
            Query.modified,
        )
        .groupby(Query.name)
        .orderby(Query.modified, order=frappe.qb.desc)
    ).run(as_dict=True)


@frappe.whitelist()
def create_query(title, data_source, table):
    query = frappe.new_doc("Query")
    query.title = title
    query.data_source = data_source
    query.append(
        "tables",
        {
            "table": table.get("value"),
            "label": table.get("label"),
        },
    )
    query.save()
    return query.name


@frappe.whitelist()
def get_operator_list(fieldtype=None):
    operator_list = [
        {"label": "equals", "value": "="},
        {"label": "not equals", "value": "!="},
        {"label": "is", "value": "is"},
    ]

    if not fieldtype:
        return operator_list

    text_data_types = ("char", "varchar", "enum", "text", "longtext")
    number_data_types = ("int", "decimal", "bigint", "float", "double")
    date_data_types = ("date", "datetime", "time", "timestamp")

    fieldtype = fieldtype.lower()
    if fieldtype in text_data_types:
        operator_list += [
            {"label": "contains", "value": "contains"},
            {"label": "not contains", "value": "not contains"},
            {"label": "starts with", "value": "starts with"},
            {"label": "ends with", "value": "ends with"},
            {"label": "is one of", "value": "in"},
            {"label": "is not one of", "value": "not in"},
        ]
    if fieldtype in number_data_types:
        operator_list += [
            {"label": "is one of", "value": "in"},
            {"label": "is not one of", "value": "not in"},
            {"label": "greater than", "value": ">"},
            {"label": "smaller than", "value": "<"},
            {"label": "greater than equal to", "value": ">="},
            {"label": "smaller than equal to", "value": "<="},
            {"label": "between", "value": "between"},
        ]

    if fieldtype in date_data_types:
        operator_list += [
            {"label": "greater than", "value": ">"},
            {"label": "smaller than", "value": "<"},
            {"label": "greater than equal to", "value": ">="},
            {"label": "smaller than equal to", "value": "<="},
            {"label": "between", "value": "between"},
            {"label": "within", "value": "timespan"},
        ]

    return operator_list


@frappe.whitelist()
def get_column_menu_options(fieldtype):
    aggregation_options = []
    format_options = []

    text_data_types = ("char", "varchar", "enum", "text", "longtext")
    number_data_types = ("int", "decimal", "bigint", "float", "double")
    datetime_data_types = ("datetime", "timestamp")
    date_data_types = "date"

    fieldtype = fieldtype.lower()
    if fieldtype in text_data_types:
        aggregation_options = [
            {"label": "Group By", "value": "Group By"},
            {"label": "Count", "value": "Count"},
            # {"label": "Count of distinct", "value": "Count Distinct"},
            {"label": "Count if", "value": "Count if"},
        ]
    if fieldtype in number_data_types:
        aggregation_options = [
            {"label": "Group By", "value": "Group By"},
            {"label": "Count", "value": "Count"},
            # {"label": "Count of distinct", "value": "Count Distinct"},
            {"label": "Count if", "value": "Count if"},
            {"label": "Sum", "value": "Sum"},
            {"label": "Minimum", "value": "Min"},
            {"label": "Maximum", "value": "Max"},
            {"label": "Average", "value": "Avg"},
        ]

    if fieldtype in datetime_data_types:
        aggregation_options = [
            {"label": "Group By", "value": "Group By"},
            {"label": "Count", "value": "Count"},
            # {"label": "Count of distinct", "value": "Count Distinct"},
            {"label": "Count if", "value": "Count if"},
            {"label": "Minimum", "value": "Min"},
            {"label": "Maximum", "value": "Max"},
        ]
        format_options = [
            {"label": "Minute", "value": "Minute"},
            {"label": "Hour", "value": "Hour"},
            {"label": "Day", "value": "Day"},
            {"label": "Month", "value": "Month"},
            {"label": "Year", "value": "Year"},
            {"label": "Minute of Hour", "value": "Minute of Hour"},
            {"label": "Hour of Day", "value": "Hour of Day"},
            {"label": "Day of Week", "value": "Day of Week"},
            {"label": "Day of Month", "value": "Day of Month"},
            {"label": "Day of Year", "value": "Day of Year"},
            {"label": "Month of Year", "value": "Month of Year"},
            {"label": "Quarter of Year", "value": "Quarter of Year"},
        ]

    if fieldtype in date_data_types:
        aggregation_options = [
            {"label": "Group By", "value": "Group By"},
            {"label": "Count", "value": "Count"},
            # {"label": "Count of distinct", "value": "Count Distinct"},
            {"label": "Count if", "value": "Count if"},
            {"label": "Minimum", "value": "Min"},
            {"label": "Maximum", "value": "Max"},
        ]
        format_options = [
            {"label": "Year", "value": "Year"},
            {"label": "Month", "value": "Month"},
            {"label": "Day", "value": "Day"},
            {"label": "Quarter of Year", "value": "Quarter of Year"},
            {"label": "Month of Year", "value": "Month of Year"},
            {"label": "Day of Year", "value": "Day of Year"},
            {"label": "Day of Month", "value": "Day of Month"},
            {"label": "Day of Week", "value": "Day of Week"},
        ]

    return {
        "aggregation_options": aggregation_options,
        "format_options": format_options,
    }
