import json
import re
from typing import Any, Dict
from google import genai  # type: ignore
from google.genai import types

genai_client = genai.Client()


def analyze_transcript_content(transcript_data: Dict) -> Dict[str, Any]:
    """
    Analyze the transcript content to extract key insights about the interview.
    """

    # Prepare the request structure for the model
    model_request = {
        "model": "gemini-2.5-flash",
        "config": types.GenerateContentConfig(
            system_instruction="""
                You are a highly skilled AI recruitment analyst trained in behavioral psychology, technical evaluation, and fair-hiring practices.
Your task is to analyze a structured interview transcript provided in JSON format and generate an objective, bias-free, and role-aligned hiring report in JSON format.
Use best practices in recruitment to evaluate the candidate’s communication, domain expertise, confidence, problem-solving ability, soft skills, and technical depth.
Do not penalize for language fluency or grammar if the candidate demonstrates strong technical understanding or clear problem-solving ability.

🔍 Input JSON Format:
{
  "items": [ 
    { "id": "...", "type": "message", "role": "assistant" | "user", "content": ["..."], "interrupted": true | false } 
  ]
}
📤 Output JSON Format:
{
  "candidateOverview": {
    "candidateName": "<Candidate Name>",
    "roleApplied": "<Job Title>",
    "communicationSkills": 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10,
    "confidenceLevel": 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10,
    "domainKnowledge": 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10,
    "problemSolvingSkills": 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10,
    "culturalFit": ""
  },
  "interviewStatistics": {
    "totalQuestionsAsked": 0,
    "totalCandidateResponses": 0,
    "estimatedDurationMinutes": 0,
    "candidateTalkRatioPercent": 0,
    "technicalToBehavioralRatio": "",
    "keywordsMentioned": [],
    "positiveIndicators": [],
    "negativeIndicators": []
  },
  "behavioralAnalysis": {
    "leadership": "",
    "communicationClarity": "",
    "adaptability": "",
    "teamCollaboration": "",
    "emotionalIntelligence": ""
  },
  "technicalEvaluation": {
    "mainChallengesDiscussed": [],
    "solutionsProposed": [],
    "technicalDepth": "",
    "alignmentWithRoleRequirements": "",
    "toolsOrTechnologiesMentioned": []
  },
  "biasCheck": {
    "grammarFluencyIssues": false,
    "didAffectScoring": false,
    "notes": ""
  },
  "hiringRecommendation": {
    "status": "",
    "reasoning": ""
  },
  "improvementSuggestions": [
    "",
    ""
  ],
  "sentimentToneAnalysis": {
    "overallSentiment": "",
    "toneBreakdown": {
      "confidence": "",
      "hesitation": "",
      "enthusiasm": "",
      "engagement": ""
    },
    "languageObservations": []
  },
  "overallSuitabilityScore": {
    "combinedScoreOutOf10": 0,
    "comparisonToPreviousRounds": "",
    "finalVerdict": ""
  }
}
            
            """
        ),
        "contents": json.dumps(transcript_data),
    }

    # Send the request to the model
    model_response = genai_client.models.generate_content(**model_request)

    try:
        # Remove any code block markers (e.g., ```json ... ```) before parsing
        cleaned_response = re.sub(
            r"```(?:json)?(.*?)```", r"\1", model_response.text.strip(), flags=re.DOTALL) # type: ignore
        # model_response may include markdown fences; remove them and parse JSON
        parsed_data = json.loads(cleaned_response)

    except Exception as e:
        return {
            "error": f"Failed to parse model response as JSON: {e}",
            "raw_response": model_response.text.strip() # type: ignore
        }

    if not parsed_data:
        return {
            "error": "No analysis data returned from the model."
        }

    return {
        "room_name": transcript_data.get("room_name"),
        "analysis": parsed_data,
        "status": "completed"
    }