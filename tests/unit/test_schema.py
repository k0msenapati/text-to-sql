from text_to_sql.db.schema import get_schema, get_schema_dict, get_table_columns


def test_get_schema_returns_formatted_ddl_string():
    """Verify that get_schema returns a clean, human-readable SQL DDL string."""
    schema = get_schema()
    assert isinstance(schema, str)
    assert "-- Table: customers" in schema
    assert "CREATE TABLE customers" in schema
    assert "-- Table: orders" in schema
    assert "CREATE TABLE orders" in schema
    # Ensure it's not a python dictionary repr
    assert not schema.startswith("{")


def test_get_schema_dict_returns_dict():
    """Verify that get_schema_dict returns the raw table_name -> CREATE SQL mapping."""
    schema_dict = get_schema_dict()
    assert isinstance(schema_dict, dict)
    assert "customers" in schema_dict
    assert "orders" in schema_dict
    assert "CREATE TABLE" in schema_dict["customers"]


def test_get_table_columns():
    """Verify column metadata retrieval."""
    cols = get_table_columns("customers")
    col_names = [c["name"] for c in cols]
    assert "customer_id" in col_names
    assert "name" in col_names
    assert "email" in col_names
