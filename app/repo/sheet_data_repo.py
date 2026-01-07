"""Sheet data repository for database operations."""

from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.models.sheet_connection import SheetRawData


class SheetDataRepository:
    """Repository for sheet raw data database operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize SheetDataRepository with database instance.

        Args:
            db: AsyncIOMotorDatabase instance
        """
        self.collection = db.sheet_raw_data

    async def upsert(
        self,
        connection_id: str,
        row_number: int,
        data: dict,
        raw_data: dict,
    ) -> SheetRawData:
        """Upsert a row of sheet data.

        If a document with the same connection_id and row_number exists,
        it will be updated. Otherwise, a new document will be created.

        Args:
            connection_id: Connection ID this data belongs to
            row_number: Row number in the sheet
            data: Mapped data (after column mapping)
            raw_data: Original row data

        Returns:
            Upserted SheetRawData instance
        """
        now = datetime.now(timezone.utc)

        result = await self.collection.find_one_and_update(
            {"connection_id": connection_id, "row_number": row_number},
            {
                "$set": {
                    "connection_id": connection_id,
                    "row_number": row_number,
                    "data": data,
                    "raw_data": raw_data,
                    "synced_at": now,
                },
            },
            upsert=True,
            return_document=True,
        )

        result["_id"] = str(result["_id"])
        return SheetRawData(**result)

    async def find_by_connection_id(
        self,
        connection_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SheetRawData], int]:
        """Find all sheet data for a connection with pagination.

        Args:
            connection_id: Connection ID to search for
            page: Page number (1-indexed)
            page_size: Number of records per page

        Returns:
            Tuple of (list of SheetRawData instances, total count)
        """
        # Calculate skip value
        skip = (page - 1) * page_size

        # Get total count
        total = await self.collection.count_documents({"connection_id": connection_id})

        # Get paginated results sorted by row_number
        cursor = (
            self.collection.find({"connection_id": connection_id})
            .sort("row_number", 1)
            .skip(skip)
            .limit(page_size)
        )

        data_list = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            data_list.append(SheetRawData(**doc))

        return data_list, total

    async def delete_by_connection_id(self, connection_id: str) -> int:
        """Delete all sheet data for a connection.

        Args:
            connection_id: Connection ID to delete data for

        Returns:
            Number of documents deleted
        """
        result = await self.collection.delete_many({"connection_id": connection_id})
        return result.deleted_count
