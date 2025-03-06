At Beekeeper, PostgreSQL databases are our primary data-store type. We typically use a one-schema per domain/micro-service format.
Bellow we present some guidelines on schema design:

# Schema Design <a href="#100" id="100">[100]</a>

## MUST make use of tenant identifier column in all tables <a href="#101" id="101">[101]</a>

All tables in all schemas must have a tenant identifier column such as tenant_id or tenant_fqdn in order to enable easy data operations on the tenant level.

## MUST make use of index on tenant identifier column in all tables <a href="#102" id="102">[102]</a>

All tables must also have an index on the tenant identifier column to allow for fast queries on the tenant level

### MUST make use of standardized column names <a href="#103" id="103">[103]</a>

Standardized column names:
| What the column stores                        | Column Name  |
|-----------------------------------------------|--------------|
| Tenant identifier                             | tenant_id    |
| Tenant FQDN                                   | tenant_fqdn  |
| The timestamp when the entity was created     | created_at   |
| The timestamp when the entity was updated last| updated_at   |
| Metadata                                      | metadata     |
| User identifier                               | user_id      |
| User name                                     | user_name    |


## SHOULD use meaningful column names <a href="#104" id="104">[104]</a>

Columns should have readable, meaningful names that accurately reflect the data they contain. Avoid using abbreviations or acronyms that may be unclear to others.

Examples:
- created_at instead of date
- title instead of text

## SHOULD use snake case column names <a href="#105" id="105">[105]</a>

Snake case refers to the writing style where each word is written in lowercase, and words are separated by underscores. For example, tenant_id or user_name. This naming convention increases readability, consistency, and ease of interpretation across your database

## SHOULD avoid numeric based enums <a href="#106" id="106">[106]</a>

Numeric values for enumerations (enums) should be avoided. Numeric enums can reduce code readability and make it more difficult for developers to understand the meaning behind the values. Instead, consider using descriptive string values for your enums to improve clarity and maintainability.

Numeric based enums are also prone to breaking.

String enums should be preferred instead.

MAY utilize JSON or JSONB data types for flexible and dynamic data storage, if applicable. [107]

These data types can be particularly useful when you are dealing with data that is variable or complex in structure. JSON and JSONB allow you to store data in a more flexible, dynamic way, which may prove beneficial for certain applications. It’s a good way of storing unstructured or semi-structured data within a relational database. They offer flexibility and are ideal for data whose structure might change over time

# Schema Interactions <a href="#200" id="200">[200]</a>

## SHOULD utilize transactions to maintain data integrity <a href="#201" id="201">[201]</a>

Transactions allow for atomicity, which means that a series of database operations are treated as a single unit, and either all operations are completed successfully or none at all. This prevents any inconsistencies or errors that could compromise the integrity of our data.

## SHOULD avoid using foreign keys unless absolutely necessary <a href="#202" id="202">[202]</a>

Foreign keys add overhead to insert, update, and delete operations. Each time a modification is done on a table that has foreign key constraints, the database management system (DBMS) must check to ensure that these constraints are still valid. This extra work can slow down the operation, which can be a concern in a system that needs high performance or has a large amount of data.

In addition, foreign keys complicate migrations.

## MUST avoid cascading deletes <a href="#203" id="203">[203]</a>

Cascading deletes can lead to unintended data loss. If a developer isn't aware that a cascade delete is set up on a certain relationship, they might delete a record, assuming only that record will be affected, and inadvertently wipe out numerous related records.

Moreover, it adds hidden complexity to your system. The behavior is defined in the schema, and might not be immediately apparent in your application code, which can make it hard for developers to reason about the system's behavior.

In addition, it makes it harder to recover from mistakes. If a row is accidentally deleted, it's not just a matter of recovering that row, but all the related rows that were automatically deleted as well.

But perhaps the most important aspect: cascading operations are not replicated by Debezium, which we rely on heavily to bring domain events onto Kafka

## MUST NOT utilize stored procedures <a href="#204" id="204">[204]</a>

Stored procedures are a powerful feature offered by most relational databases. They allow for SQL code to be stored on the database server and executed as a unit, which can increase efficiency and security.

However, there are several reasons why you might want to avoid stored procedures:

Portability: Stored procedures are often written in proprietary languages or extensions of SQL, which can make your application less portable between different types of databases.

Debugging: Stored procedures run on the database server, which can make them harder to debug than application code that runs on the application server.

Version control: It's often harder to keep track of changes to stored procedures, and keep them in sync with your application code, than it is with code that's stored in your application's version control system.

## SHOULD  use UTC only timestamps <a href="#205" id="205">[205]</a>

When storing timestamps in a database, it is usually best practice to store them in Coordinated Universal Time (UTC) rather than in a local timezone. This is because UTC does not have daylight saving time and is not subject to changes in local timezone laws, which makes it a stable reference point.

Storing timestamps in UTC can avoid confusion and potential errors when your system is used across different timezones. For example, if you have users or servers in different timezones, and you store timestamps in a local timezone, you will have to convert between timezones, which can be complex and error-prone. By using UTC, you can avoid this complexity.

## SHOULD evaluate query performance before shipping to production <a href="#206" id="206">[206]</a>

Before committing code that queries the DB, especially one that will be used frequently or on large amounts of data, it is a best practice to evaluate its performance. This is especially important for microservices since all of them run their DBs on the same physical server! One single badly written query can start hindering performance in all of them!

Performance evaluation can involve a few different steps:

Explain Plans: Almost all SQL databases have a command (typically EXPLAIN) that allows you to see the plan the database will use to execute your query. This can tell you whether the database is able to use an index to speed up the query, how many rows it estimates it will need to process, and other useful information.

Run the Query on a Subset of Data: If your database is large, it may be impractical to run the full query for testing purposes. Instead, you can run it on a subset of your data to get an idea of how it performs.

Check Resource Usage: This is easy to do in AWS by going to RDS Performance Insights and seeing which queries take the most resources

More formalized process coming soon. TBD.

## MAY utilize over-filtering for better performance <a href="#207" id="207">[207]</a>

Over-filtering refers to the practice of filtering out unnecessary data as early as possible in the query process. The goal is to reduce the amount of data that needs to be processed in later stages of the query, which can improve the overall performance.

For example, if you're joining multiple tables, you might choose to filter the tables before the join operation rather than after. This can reduce the number of rows that need to be joined, which can significantly decrease the time it takes to perform the join, especially for large tables.

Over-filtering can also be useful when you're dealing with aggregated data. If you can filter out unneeded rows before performing the aggregation, you can potentially save a lot of computation.

## MAY use multicolumn indices<a href="#208" id="208">[208]</a>

A multicolumn index can be beneficial when you frequently query data using multiple columns in the WHERE clause. By including those columns in your index, you can make those queries faster.

However, multicolumn indices should be used judiciously as they have a space cost and can slow down write operations. The index needs to be updated every time a write operation (INSERT, UPDATE, DELETE) happens on the indexed columns, which can impact performance

## MAY utilize covering indices <a href="#209" id="209">[209]</a>

A covering index is an index that includes all the columns that are needed to process a particular query. By including all necessary columns in the index, the database can fulfill the query just by looking at the index, without having to go to the table itself. This can significantly improve the performance of your queries.

Like multicolumn indices, however, covering indices should be used judiciously. They can take up more space and slow down write operations, so you need to balance the benefits against the costs.
