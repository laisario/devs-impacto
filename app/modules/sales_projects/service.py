"""
Sales Projects module service.
Business logic for Projeto de Venda operations.
"""

import uuid
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.errors import NotFoundError, ValidationError
from app.modules.producers.schemas import ProducerType
from app.modules.sales_projects.pdf_generator import generate_sales_project_pdf
from app.modules.sales_projects.schemas import (
    ProjectItem,
    ProjectStatus,
    SalesProjectCreate,
    SalesProjectInDB,
    SalesProjectWithDetails,
)
from app.shared.utils import to_object_id, utc_now


class SalesProjectsService:
    """Service for sales projects operations."""

    def __init__(self, db: AsyncIOMotorDatabase):  # type: ignore[type-arg]
        self.db = db
        self.collection = db.sales_projects
        self.calls_collection = db.calls_for_proposals
        self.profiles_collection = db.producer_profiles

    async def create_project(
        self,
        user_id: str,
        data: SalesProjectCreate,
    ) -> SalesProjectInDB:
        """
        Create a new sales project.

        Validates that:
        - Call exists
        - User has a producer profile

        Args:
            user_id: User's MongoDB ObjectId as string
            data: Sales project data

        Returns:
            Created sales project

        Raises:
            NotFoundError: If call or producer profile not found
            ValidationError: If validation fails
        """
        user_oid = to_object_id(user_id)

        # Validate call exists
        try:
            call_oid = to_object_id(data.call_id)
        except ValueError:
            raise ValidationError("ID da chamada pública inválido") from None

        call = await self.calls_collection.find_one({"_id": call_oid})
        if not call:
            raise NotFoundError("Chamada pública", data.call_id)

        # Validate user has producer profile
        profile = await self.profiles_collection.find_one({"user_id": user_oid})
        if not profile:
            raise ValidationError(
                "Perfil de produtor não encontrado",
                detail="Crie seu perfil de produtor antes de criar um projeto de venda",
            )

        # Calculate total value
        total_value = sum(item.quantity * item.unit_price for item in data.items)
        total_value = round(total_value, 2)

        now = utc_now()

        # Prepare items for storage (include computed total)
        items_data = [item.model_dump() for item in data.items]

        doc = {
            "user_id": user_oid,
            "call_id": call_oid,
            "producer_profile_id": profile["_id"],
            "items": items_data,
            "total_value": total_value,
            "status": ProjectStatus.DRAFT.value,
            "generated_pdf_url": None,
            "created_at": now,
            "updated_at": now,
        }

        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id

        return SalesProjectInDB(**doc)

    async def get_project_by_id(
        self,
        project_id: str,
        user_id: str,
    ) -> SalesProjectInDB | None:
        """
        Get a sales project by ID.

        Args:
            project_id: Project's MongoDB ObjectId as string
            user_id: User's MongoDB ObjectId (for ownership check)

        Returns:
            Sales project if found and owned by user, None otherwise
        """
        try:
            project_oid = to_object_id(project_id)
            user_oid = to_object_id(user_id)
        except ValueError:
            return None

        doc = await self.collection.find_one(
            {
                "_id": project_oid,
                "user_id": user_oid,
            }
        )

        if not doc:
            return None

        # Convert items to ProjectItem objects
        doc["items"] = [ProjectItem(**item) for item in doc["items"]]

        return SalesProjectInDB(**doc)

    async def get_project_with_details(
        self,
        project_id: str,
        user_id: str,
    ) -> SalesProjectWithDetails | None:
        """
        Get a sales project with all related data for PDF generation.

        Args:
            project_id: Project's MongoDB ObjectId as string
            user_id: User's MongoDB ObjectId

        Returns:
            Sales project with call and producer details
        """
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            return None

        # Get call
        call = await self.calls_collection.find_one({"_id": project.call_id})
        if not call:
            return None

        # Get producer profile
        profile = await self.profiles_collection.find_one({"_id": project.producer_profile_id})
        if not profile:
            return None

        # Determine producer document (CNPJ or CPF)
        producer_type = profile.get("producer_type", "individual")
        if producer_type == ProducerType.FORMAL.value:
            producer_document = profile.get("cnpj", "")
        else:
            producer_document = profile.get("cpf", "")

        return SalesProjectWithDetails(
            project=project,
            call_number=call["number"],
            call_entity_name=call["entity_name"],
            call_entity_cnpj=call["entity_cnpj"],
            producer_name=profile["name"],
            producer_type=producer_type,
            producer_document=producer_document,
            producer_dap_caf=profile.get("dap_caf_number", ""),
            producer_address=profile.get("address", ""),
            producer_city=profile.get("city", ""),
            producer_state=profile.get("state", ""),
        )

    async def generate_pdf(
        self,
        project_id: str,
        user_id: str,
    ) -> str:
        """
        Generate PDF for a sales project.

        Args:
            project_id: Project's MongoDB ObjectId as string
            user_id: User's MongoDB ObjectId

        Returns:
            URL of the generated PDF

        Raises:
            NotFoundError: If project not found
        """
        # Get project with all details
        details = await self.get_project_with_details(project_id, user_id)
        if not details:
            raise NotFoundError("Projeto de venda", project_id)

        # Generate PDF
        pdf_content = generate_sales_project_pdf(details)

        # Save PDF (mock storage - saves to local file)
        # In production, would upload to S3/GCS
        pdf_filename = f"projeto_venda_{project_id}_{uuid.uuid4().hex[:8]}.pdf"

        # Create pdfs directory if it doesn't exist
        pdf_dir = Path("generated_pdfs")
        pdf_dir.mkdir(exist_ok=True)

        pdf_path = pdf_dir / pdf_filename
        pdf_path.write_bytes(pdf_content)

        # Mock URL (in production, would be S3/GCS URL)
        pdf_url = f"{settings.mock_storage_base_url}/pdfs/{pdf_filename}"

        # Update project with PDF URL
        await self.collection.update_one(
            {"_id": to_object_id(project_id)},
            {
                "$set": {
                    "generated_pdf_url": pdf_url,
                    "updated_at": utc_now(),
                }
            },
        )

        return pdf_url

