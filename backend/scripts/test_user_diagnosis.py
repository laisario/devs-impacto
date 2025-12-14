#!/usr/bin/env python3
"""
Test script to check diagnosis and recommendations for a specific CPF.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from motor.motor_asyncio import AsyncIOMotorClient
from app.modules.auth.service import AuthService
from app.modules.onboarding.service import OnboardingService
from app.modules.formalization.service import FormalizationService
from app.modules.formalization.diagnosis import calculate_eligibility


async def test_user_diagnosis(cpf: str):
    """Test diagnosis for a specific CPF."""
    # Connect to MongoDB
    mongodb_uri = "mongodb+srv://admin:jQs2xrlrLhK6Ure3@hackasdb.bhcckki.mongodb.net/"
    client = AsyncIOMotorClient(mongodb_uri)
    db = client.get_database("hackathon")
    
    try:
        # Get user
        auth_service = AuthService(db)
        user_doc = await auth_service.collection.find_one({"cpf": cpf})
        
        if not user_doc:
            print(f"❌ User with CPF {cpf} not found!")
            print("Creating user...")
            token = await auth_service.login(cpf)
            user_doc = await auth_service.collection.find_one({"cpf": cpf})
            print(f"✅ User created! Token: {token[:50]}...")
        
        user_id = str(user_doc["_id"])
        print(f"\n📋 User ID: {user_id}")
        print(f"📋 CPF: {cpf}")
        
        # Get onboarding answers
        onboarding_service = OnboardingService(db)
        answers = await onboarding_service.get_all_answers(user_id)
        
        print(f"\n📝 Onboarding Answers ({len(answers)} answers):")
        if not answers:
            print("  ⚠️  No onboarding answers found!")
        else:
            for qid, answer_doc in answers.items():
                print(f"  - {qid}: {answer_doc.answer}")
        
        # Convert to simple dict
        responses = {qid: ans.answer for qid, ans in answers.items()}
        
        # Calculate diagnosis
        print(f"\n🔍 Calculating Diagnosis...")
        diagnosis = calculate_eligibility(responses)
        
        print(f"\n📊 Diagnosis Results:")
        print(f"  - Is Eligible: {diagnosis['is_eligible']}")
        print(f"  - Eligibility Level: {diagnosis['eligibility_level']}")
        print(f"  - Score: {diagnosis['score']}/100")
        print(f"  - Requirements Met: {diagnosis['requirements_met']}")
        print(f"  - Requirements Missing: {diagnosis['requirements_missing']}")
        print(f"  - Recommendations: {diagnosis['recommendations']}")
        
        # Get formalization service
        formalization_service = FormalizationService(db)
        
        # Get status (will sync tasks)
        print(f"\n🔄 Getting formalization status (will sync tasks)...")
        status = await formalization_service.get_or_calculate_status(user_id)
        
        print(f"\n📈 Formalization Status:")
        print(f"  - Is Eligible: {status.is_eligible}")
        print(f"  - Eligibility Level: {status.eligibility_level}")
        print(f"  - Score: {status.score}/100")
        print(f"  - Requirements Met: {status.requirements_met}")
        print(f"  - Requirements Missing: {status.requirements_missing}")
        print(f"  - Recommendations: {status.recommendations}")
        
        # Get tasks
        print(f"\n📋 Getting Tasks...")
        tasks = await formalization_service.get_tasks(user_id)
        
        print(f"\n✅ Tasks Generated ({len(tasks)} tasks):")
        if not tasks:
            print("  ⚠️  No tasks generated!")
        else:
            for task in tasks:
                print(f"  - {task.task_id}: {task.title}")
                print(f"    Priority: {task.priority}, Category: {task.category}")
                print(f"    Requirement ID: {task.requirement_id}")
                print(f"    Completed: {task.completed}")
                print()
        
        # Check what's missing
        print(f"\n🔎 Analysis:")
        if not diagnosis['requirements_missing']:
            print("  ✅ All requirements are met!")
        else:
            print(f"  ⚠️  Missing requirements: {', '.join(diagnosis['requirements_missing'])}")
        
        if not diagnosis['recommendations']:
            print("  ⚠️  No recommendations generated!")
        else:
            print(f"  💡 Recommendations:")
            for rec in diagnosis['recommendations']:
                print(f"    - {rec}")
        
        if not tasks:
            print("  ⚠️  No tasks generated! This might be the issue.")
            print("  💡 Possible reasons:")
            print("    - All requirements are met (no tasks needed)")
            print("    - Questions mapping is not working correctly")
            print("    - generate_formalization_tasks is not creating tasks")
        
    finally:
        client.close()


if __name__ == "__main__":
    cpf = "16914918708"
    print(f"🧪 Testing diagnosis for CPF: {cpf}\n")
    asyncio.run(test_user_diagnosis(cpf))
