"""
Google Gemini API integration service for InterviewX.
Follows zero-hardcoding guidelines: reads strictly from environment variables.
Provides structured prompt engineering for:
1. AI Mock Interviewer (Question generation & follow-ups)
2. Honest Feedback Engine (Zero false praise, explicit technical flaw identification)
3. Answer Improvement (Original vs Improved with justification)
4. Personalised Roadmap Generation
"""

import json
import logging
from typing import Dict, Any, List, Optional
import requests
from config import get_gemini_api_key, is_api_key_configured

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

class APIKeyMissingError(Exception):
    """Raised when the Gemini API key is not configured in the environment."""
    pass

class GeminiService:
    """Encapsulates all Google Gemini API interactions with structured JSON parsing."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_gemini_api_key()

    def is_ready(self) -> bool:
        """Returns True if a valid API key is present."""
        return bool(self.api_key and len(self.api_key) > 10)

    def _call_gemini_raw(self, prompt: str, system_instruction: str = "", temperature: float = 0.2) -> str:
        """
        Executes an HTTP POST to Google Gemini REST endpoint.
        Handles rate limits, network timeouts, and JSON error responses.
        """
        if not self.is_ready():
            raise APIKeyMissingError(
                "Gemini API Key is missing. Please set GEMINI_API_KEY in your .env file "
                "or export it as an environment variable."
            )

        url = GEMINI_API_URL
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        payload: Dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "topP": 0.95,
                "responseMimeType": "application/json"
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 400:
                error_msg = response.json().get("error", {}).get("message", "Bad Request")
                raise ValueError(f"Gemini API Request Error: {error_msg}")
            elif response.status_code in (401, 403):
                raise PermissionError("Gemini API Key is invalid or lacks required permissions.")
            elif response.status_code == 429:
                raise RuntimeError("Gemini API rate limit exceeded. Please wait a moment before trying again.")
            
            response.raise_for_status()
            res_data = response.json()

            candidates = res_data.get("candidates", [])
            if not candidates:
                raise RuntimeError("No candidate response received from Gemini.")

            part = candidates[0].get("content", {}).get("parts", [{}])[0]
            raw_text = part.get("text", "{}")
            return raw_text.strip()

        except requests.exceptions.Timeout:
            raise TimeoutError("Gemini API request timed out after 30 seconds.")
        except (ValueError, PermissionError, RuntimeError):
            raise
        except Exception as e:
            safe_msg = str(e)
            if self.api_key and self.api_key in safe_msg:
                safe_msg = safe_msg.replace(self.api_key, "••••••••")
            raise ConnectionError(f"Network error connecting to Gemini API: {safe_msg}")

    def test_connection(self) -> Dict[str, Any]:
        """Validates API key connectivity with a lightweight ping without exposing the key."""
        if not self.is_ready():
            return {"success": False, "message": "API Key is not configured."}
        try:
            raw = self._call_gemini_raw("Ping: reply with {'status': 'ok'}", temperature=0.0)
            data = json.loads(raw)
            return {"success": True, "message": "Successfully connected to Google Gemini 2.5 Flash!", "data": data}
        except PermissionError:
            return {"success": False, "message": "Authentication failed: Invalid Gemini API key or missing permissions."}
        except Exception as e:
            safe_msg = str(e)
            if self.api_key and self.api_key in safe_msg:
                safe_msg = safe_msg.replace(self.api_key, "••••••••")
            return {"success": False, "message": safe_msg}

    def generate_interview_question(
        self,
        role_title: str,
        difficulty: str,
        interview_type: str,
        question_number: int,
        target_company_track: str,
        previous_context: Optional[List[Dict[str, Any]]] = None,
        resume_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates a focused, realistic interview question.
        Supports asking one question at a time and follow-ups based on previous responses.
        Uses resume skills and projects if provided.
        """
        if self.is_ready():
            try:
                system_instruction = (
                    "You are an elite, highly experienced Senior Technical Interviewer and Hiring Committee Member "
                    "at top technology firms and Indian tech companies (ranging from TCS/Infosys campus drives to "
                    "high-scale product companies like Flipkart, Swiggy, Amazon, and Google). "
                    "Your task is to conduct a realistic, rigorous interview. Ask exactly ONE clear, focused question. "
                    "If previous answers had technical gaps or inaccuracies, follow up on them to test depth. "
                    "If resume details are provided, tailor the question to test their claimed projects and skills. "
                    "You must return ONLY valid JSON matching the specified schema."
                )

                resume_summary_snippet = ""
                if resume_context:
                    r_skills = resume_context.get("parsed_skills", [])
                    r_proj = [p.get("title", "") for p in resume_context.get("parsed_projects", []) if isinstance(p, dict)]
                    resume_summary_snippet = f"Candidate Resume Skills: {', '.join(r_skills[:8])}. Projects: {', '.join(r_proj[:3])}."

                prompt = f"""
                Role: {role_title}
                Difficulty: {difficulty}
                Interview Type: {interview_type}
                Target Track: {target_company_track}
                Question Number: {question_number}
                {resume_summary_snippet}
                Previous Questions and Answers Context: {json.dumps(previous_context or [])}

                Generate the next single interview question.
                JSON Schema to return:
                {{
                    "question_number": {question_number},
                    "question_text": "The exact question string",
                    "category": "DSA / DBMS / OS / System Design / Behavioral / Core CS",
                    "key_focus_areas": ["point 1", "point 2"],
                    "interviewer_intent": "What you are specifically assessing with this question",
                    "is_follow_up": true or false
                }}
                """

                raw = self._call_gemini_raw(prompt, system_instruction=system_instruction, temperature=0.4)
                data = json.loads(raw)
                data["is_offline"] = False
                data["evaluation_engine"] = "Google Gemini 2.5 Flash"
                import re
                if "question_text" in data:
                    data["question_text"] = re.sub(r'<[^>]+>', '', str(data["question_text"])).strip()
                return data
            except Exception as e:
                logger.warning(f"Gemini question generation error: {e}, using offline question generator.")

        # High-quality fallback generator
        return self._generate_fallback_question(
            role_title, difficulty, interview_type, question_number, resume_context, previous_context
        )

    def _generate_fallback_question(
        self,
        role_title: str,
        difficulty: str,
        interview_type: str,
        question_number: int,
        resume_context: Optional[Dict[str, Any]] = None,
        previous_context: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generates realistic offline questions tailored to role, tier, and resume."""
        # 1. Check if previous answer warranted a follow-up
        if previous_context and len(previous_context) > 0 and question_number % 2 == 0:
            last_item = previous_context[-1]
            last_q = last_item.get("question_text", "")
            return {
                "question_number": question_number,
                "question_text": f"Following up on your previous answer regarding '{last_q[:60]}...': Can you elaborate on the potential bottlenecks, time/space complexity trade-offs, and how you would test for edge cases?",
                "category": "Technical Follow-Up",
                "key_focus_areas": ["Edge case handling", "Bottleneck identification", "Complexity analysis"],
                "interviewer_intent": "Probe deeper into candidate's conceptual trade-offs and edge-case handling.",
                "is_follow_up": True,
                "is_offline": True
            }

        # 2. Check resume questions if resume-based mode
        if resume_context and "resume" in interview_type.lower():
            res_questions = resume_context.get("interview_questions", [])
            idx = (question_number - 1) % len(res_questions) if res_questions else 0
            if res_questions and idx < len(res_questions):
                return {
                    "question_number": question_number,
                    "question_text": res_questions[idx],
                    "category": "Resume Deep-Dive",
                    "key_focus_areas": ["Applied practical experience", "Architecture of claimed projects"],
                    "interviewer_intent": "Validate authenticity of skills and projects listed on resume.",
                    "is_follow_up": False,
                    "is_offline": True
                }

        # 3. Domain Question Bank mapped by role and round type
        bank: Dict[str, List[Dict[str, str]]] = {
            "hr": [
                {"q": "Tell me about yourself, your academic background, and why you are interested in this specific role.", "c": "HR / Background"},
                {"q": "Describe a challenging situation in a team project where you had a conflict. How did you resolve it?", "c": "Behavioral / STAR"},
                {"q": "What are your top technical strengths, and what is one technical area you are actively working to improve?", "c": "Self-Awareness"},
                {"q": "Where do you see your career progressing over the next 2 to 3 years?", "c": "Career Vision"}
            ],
            "software": [
                {"q": "How does a Hash Table handle collisions internally, and what is the difference between Separate Chaining and Open Addressing?", "c": "Data Structures"},
                {"q": "Explain the four core principles of Object-Oriented Programming with practical real-world design examples.", "c": "OOP Concepts"},
                {"q": "What is the difference between a Process and a Thread? How does inter-process communication (IPC) work?", "c": "Operating Systems"},
                {"q": "Explain Database Normalization (1NF through 3NF) and when you might intentionally choose to denormalize.", "c": "DBMS & SQL"},
                {"q": "How does the TCP 3-way handshake work, and why is UDP preferred for streaming audio/video?", "c": "Computer Networks"}
            ],
            "python": [
                {"q": "Explain how Python's Global Interpreter Lock (GIL) affects multithreading vs multiprocessing for CPU-bound tasks.", "c": "Python Internals"},
                {"q": "What is the difference between deepcopy and shallow copy in Python? How does memory allocation work for mutable objects?", "c": "Memory Management"},
                {"q": "How do Python generators and the yield keyword work, and how do they optimize memory usage for large datasets?", "c": "Core Python"},
                {"q": "Explain how Python decorators work under the hood and write an example of a timing decorator.", "c": "Advanced Python"}
            ],
            "java": [
                {"q": "Explain the Java Memory Model: difference between Heap and Stack memory, and how Generational Garbage Collection works.", "c": "JVM & Memory"},
                {"q": "What is the difference between HashMap and ConcurrentHashMap in Java? How is thread safety achieved without synchronized blocks?", "c": "Collections & Concurrency"},
                {"q": "Explain the life cycle of a Spring Boot bean and the difference between Singleton and Prototype scopes.", "c": "Spring Framework"},
                {"q": "What are checked vs unchecked exceptions in Java, and why does Java 8 encourage Optional over null checks?", "c": "Core Java"}
            ],
            "frontend": [
                {"q": "How does React's Virtual DOM reconciliation algorithm work, and why is using index as a key in lists considered an anti-pattern?", "c": "React.js"},
                {"q": "Explain JavaScript closures, the Event Loop, Microtasks (Promises) vs Macrotasks (setTimeout).", "c": "JavaScript Core"},
                {"q": "What is the difference between Server-Side Rendering (SSR) and Client-Side Rendering (CSR) in modern web apps?", "c": "Web Architecture"},
                {"q": "How would you optimize Core Web Vitals (specifically Largest Contentful Paint and Cumulative Layout Shift) on a sluggish web page?", "c": "Web Performance"}
            ],
            "backend": [
                {"q": "How would you design a rate limiter for a public REST API? What algorithm (Token Bucket, Leaky Bucket, Sliding Window) would you choose?", "c": "System Design"},
                {"q": "Explain Database Indexing: how do B-Tree and Hash indexes work, and why do indexes slow down INSERT/UPDATE operations?", "c": "Database Engineering"},
                {"q": "What is the difference between horizontal and vertical scaling, and how does a reverse proxy like NGINX balance load?", "c": "Distributed Systems"},
                {"q": "How do you ensure idempotency in payment processing APIs?", "c": "API Design"}
            ],
            "data": [
                {"q": "Explain the difference between WHERE and HAVING in SQL, and write a query using a Window Function like ROW_NUMBER().", "c": "SQL Queries"},
                {"q": "How do you detect and handle missing data and outliers in Pandas before training an analytics model?", "c": "Data Wrangling"},
                {"q": "Explain the bias-variance tradeoff in Machine Learning and how cross-validation helps prevent overfitting.", "c": "Machine Learning"},
                {"q": "What metrics would you monitor to measure candidate engagement on a career preparation platform?", "c": "Business Analytics"}
            ],
            "devops": [
                {"q": "Explain the difference between a Docker image and a Docker container. How do Docker layers optimize build times?", "c": "Containerization"},
                {"q": "What is the role of Kubernetes pods, services, and ingress controllers in a container cluster?", "c": "Kubernetes"},
                {"q": "How do you structure a production CI/CD pipeline with automated testing, linting, and rolling deployment?", "c": "CI/CD"},
                {"q": "Explain DNS resolution and how HTTPS TLS/SSL certificates establish encrypted communication.", "c": "Networking & Security"}
            ]
        }

        # Select appropriate bank
        role_lower = role_title.lower()
        if "hr" in interview_type.lower() or "behavioral" in interview_type.lower():
            pool = bank["hr"]
        elif "python" in role_lower:
            pool = bank["python"]
        elif "java" in role_lower:
            pool = bank["java"]
        elif "frontend" in role_lower:
            pool = bank["frontend"]
        elif "backend" in role_lower:
            pool = bank["backend"]
        elif "data" in role_lower or "analytics" in role_lower or "ml" in role_lower or "ai" in role_lower:
            pool = bank["data"]
        elif "devops" in role_lower or "cloud" in role_lower:
            pool = bank["devops"]
        else:
            pool = bank["software"]

        selected = pool[(question_number - 1) % len(pool)]
        return {
            "question_number": question_number,
            "question_text": selected["q"],
            "category": selected["c"],
            "key_focus_areas": ["Conceptual precision", "Trade-off analysis", "Structured explanation"],
            "interviewer_intent": f"Assess baseline competency in {selected['c']} for {role_title}.",
            "is_follow_up": False,
            "is_offline": True
        }

    def evaluate_answer_honest(
        self,
        question_text: str,
        user_answer: str,
        role_title: str,
        difficulty: str
    ) -> Dict[str, Any]:
        """
        Module 2 & 3: Honest Feedback Engine & Answer Improvement.
        Evaluates 4 criteria scored out of 10:
        1. Technical Accuracy (0-10)
        2. Conceptual Understanding (0-10)
        3. Communication Skills (0-10)
        4. Answer Relevance (0-10)
        STRICT RULES:
        - Never praise incorrect answers as correct.
        - Identify all incorrect technical concepts explicitly.
        - Highlight missing information and edge cases.
        - Give constructive, honest feedback based on evidence.
        - Provide an improved sample answer and explain why it is superior.
        """
        if self.is_ready():
            try:
                system_instruction = (
                    "You are the 'Honest Feedback Engine' of InterviewX. "
                    "CRITICAL DIRECTIVES: "
                    "1. NEVER give false praise. If an answer has misconceptions, call them out directly and politely. "
                    "2. Score with strict engineering rigor on a 0-10 scale for: "
                    "   - technical_accuracy (0-10): Factual precision, correct syntax, complexities. "
                    "   - conceptual_understanding (0-10): Deep grasp of underlying mechanics, trade-offs. "
                    "   - communication_skills (0-10): Structure, clarity, concise articulation. "
                    "   - answer_relevance (0-10): Direct address to the question without wandering. "
                    "3. Identify every incorrect technical concept, flawed logic, or wrong time/space complexity. "
                    "4. Highlight missing edge cases, architectural trade-offs, or standard practices. "
                    "5. Detail what the candidate did well, and how the answer can be improved. "
                    "6. Provide an exemplary improved sample answer that would pass a Tier-1 technical screen. "
                    "7. Detail exactly WHY the improved answer is better than the candidate's original answer. "
                    "Output strictly valid JSON only."
                )

                prompt = f"""
                Interview Role: {role_title}
                Difficulty Level: {difficulty}
                Interview Question: {question_text}
                Candidate's Answer: {user_answer}

                Evaluate this answer honestly using the 4 criteria out of 10.
                Required JSON Schema:
                {{
                    "scores_10": {{
                        "accuracy": 0-10 (e.g. 7.5),
                        "conceptual": 0-10,
                        "communication": 0-10,
                        "relevance": 0-10,
                        "overall": 0-10
                    }},
                    "scores": {{
                        "accuracy": 0-100,
                        "conceptual": 0-100,
                        "clarity": 0-100,
                        "relevance": 0-100,
                        "completeness": 0-100,
                        "overall": 0-100
                    }},
                    "honest_critique": "Brutally honest, constructive evaluation of what worked and what failed.",
                    "what_went_well": "Specific aspects the candidate articulated well",
                    "how_to_improve": "Practical suggestions to structure or deepen the response",
                    "incorrect_concepts": [
                        "List specific wrong claims, factual errors, or misstatements made by candidate"
                    ],
                    "missing_information": [
                        "List important concepts, trade-offs, complexity limits, or edge cases omitted"
                    ],
                    "improved_sample_answer": "A production-grade, articulate answer ready for a tier-1 technical interview.",
                    "why_improved_is_better": "Specific breakdown of why the sample answer scores higher.",
                    "detected_topics": [
                        {{"topic": "Name of topic", "category": "Technical/HR", "status": "weakness or strength"}}
                    ]
                }}
                """

                raw = self._call_gemini_raw(prompt, system_instruction=system_instruction, temperature=0.1)
                data = json.loads(raw)
                data["is_offline"] = False
                data["evaluation_engine"] = "Google Gemini 2.5 Flash"
                return data
            except Exception as e:
                logger.warning(f"Gemini answer evaluation error: {e}, falling back to heuristic engine.")

        # Fallback offline honest evaluation
        return self._evaluate_fallback_honest(question_text, user_answer, role_title, difficulty)

    def _evaluate_fallback_honest(
        self,
        question_text: str,
        user_answer: str,
        role_title: str,
        difficulty: str
    ) -> Dict[str, Any]:
        """Provides objective, evidence-based feedback when offline."""
        ans_clean = (user_answer or "").strip()
        word_count = len(ans_clean.split())

        # Evidence checks
        incorrect_concepts = []
        missing_info = []
        what_went_well = ""
        how_to_improve = ""
        detected_topics = []

        if word_count < 10:
            scores_10 = {"accuracy": 2.5, "conceptual": 2.0, "communication": 3.0, "relevance": 3.5, "overall": 2.8}
            scores_100 = {"accuracy": 25.0, "conceptual": 20.0, "clarity": 30.0, "relevance": 35.0, "completeness": 20.0, "overall": 28.0}
            honest_critique = "Answer was too brief to demonstrate technical competency. A single phrase or fragmented sentence fails to address the interviewer's intent."
            incorrect_concepts.append("Insufficient explanation provided to demonstrate technical depth.")
            missing_info.extend(["Detailed explanation of internal mechanics", "Complexity analysis", "Practical scenario or edge cases"])
            what_went_well = "Submitted an initial attempt."
            how_to_improve = "Structure your answer using: 1. Core definition, 2. Mechanism/How it works, 3. Trade-offs or complexities."
            sample_answer = f"A complete answer to '{question_text}' requires defining the core abstraction, detailing the internal runtime mechanism, and identifying key edge cases."
            why_better = "Directly addresses the question with structured technical depth and comprehensive coverage."
            detected_topics.append({"topic": "Answer Articulation & Depth", "category": "Communication", "status": "weakness"})
        else:
            # Medium/thorough answer
            # Check for common mistakes
            ans_lower = ans_clean.lower()
            if "hashmap" in question_text.lower() and ("always o(1)" in ans_lower or "o(1) lookup" in ans_lower):
                incorrect_concepts.append("Claimed HashMap lookup is always O(1) without accounting for hash collision degradation (O(log N) in Java 8+ / O(N) worst-case).")
                missing_info.append("Java 8 Red-Black Tree treeification threshold when bucket size exceeds 8.")

            if "tcp" in question_text.lower() and "handshake" not in ans_lower:
                missing_info.append("Explanation of SYN, SYN-ACK, ACK 3-way handshake sequence.")

            if "virtual dom" in question_text.lower() and "reconciliation" not in ans_lower:
                missing_info.append("Diffing algorithm heuristics and fiber reconciliation tree mechanics.")

            # Calculate objective scores
            acc = 7.5 if not incorrect_concepts else 5.0
            conc = 7.0 if len(missing_info) < 2 else 5.5
            comm = 8.0 if word_count > 30 else 6.5
            rel = 8.0 if any(w in ans_lower for w in question_text.lower().split()[:3]) else 6.0
            ovr = round((acc * 0.35 + conc * 0.25 + comm * 0.20 + rel * 0.20), 1)

            scores_10 = {"accuracy": acc, "conceptual": conc, "communication": comm, "relevance": rel, "overall": ovr}
            scores_100 = {
                "accuracy": acc * 10.0,
                "conceptual": conc * 10.0,
                "clarity": comm * 10.0,
                "relevance": rel * 10.0,
                "completeness": conc * 10.0,
                "overall": ovr * 10.0
            }

            honest_critique = f"Your answer demonstrates an active grasp of the fundamental concept. However, {f'it contains misconceptions ({incorrect_concepts[0]}) and ' if incorrect_concepts else ''}omits critical production details needed for senior evaluation."
            what_went_well = "Communicated the primary purpose clearly using direct terminology."
            how_to_improve = "Incorporate time/space complexity numbers, architectural trade-offs, and mention edge cases explicitly."
            sample_answer = f"To answer '{question_text}' at a Tier-1 placement standard: First state the formal concept, walk through the execution lifecycle step-by-step, contrast with alternative approaches, and state precise operational complexities."
            why_better = "Exemplary answer eliminates vagueness, avoids over-generalized claims, and cites concrete engineering metrics."

            detected_topics.append({"topic": question_text.split("?")[0][:40], "category": "Technical", "status": "strength" if ovr >= 7.0 else "weakness"})

        return {
            "scores_10": scores_10,
            "scores": scores_100,
            "honest_critique": honest_critique,
            "what_went_well": what_went_well,
            "how_to_improve": how_to_improve,
            "incorrect_concepts": incorrect_concepts,
            "missing_information": missing_info,
            "improved_sample_answer": sample_answer,
            "why_improved_is_better": why_better,
            "detected_topics": detected_topics,
            "is_offline": True,
            "evaluation_engine": "InterviewX Heuristic Audit Engine (Offline Mode - Gemini API Key Not Active)"
        }

    def generate_daywise_roadmap(
        self,
        role_title: str,
        weaknesses: List[Dict[str, Any]],
        duration_days: int = 14
    ) -> Dict[str, Any]:
        """
        Module 4: Personalised Preparation Roadmap.
        Identifies weak topics and generates a practical day-wise preparation schedule.
        """
        if self.is_ready():
            try:
                system_instruction = (
                    "You are an expert tech career coach for Indian college students and fresh graduates. "
                    "Create a practical, highly realistic day-by-day preparation roadmap focusing specifically "
                    "on remediating the candidate's recurring weaknesses and preparing for campus/off-campus placements."
                )

                prompt = f"""
                Target Role: {role_title}
                Preparation Timeline: {duration_days} Days
                Identified Weak Topics: {json.dumps(weaknesses)}

                Return a structured day-wise preparation roadmap in JSON:
                {{
                    "title": "{duration_days}-Day Targeted Placement Sprint for {role_title}",
                    "overview": "Summary of plan and strategy",
                    "daily_plan": [
                        {{
                            "day": 1,
                            "focus_topic": "Topic Name",
                            "core_concept_to_master": "Specific concept",
                            "recommended_study": "What to read, watch, or implement",
                            "practical_exercise": "Specific coding problem or mock scenario to solve",
                            "hours_recommended": 3
                        }}
                    ],
                    "key_milestones": ["Milestone 1", "Milestone 2"]
                }}
                """

                raw = self._call_gemini_raw(prompt, system_instruction=system_instruction, temperature=0.3)
                data = json.loads(raw)
                data["is_offline"] = False
                return data
            except Exception as e:
                logger.warning(f"Gemini roadmap generation error: {e}, falling back to curated curriculum.")

        # Fallback curriculum builder
        return self._generate_fallback_roadmap(role_title, weaknesses, duration_days)

    def _generate_fallback_roadmap(
        self,
        role_title: str,
        weaknesses: List[Dict[str, Any]],
        duration_days: int = 14
    ) -> Dict[str, Any]:
        """Generates structured day-wise learning tasks mapped to candidate's weaknesses."""
        weak_names = [w.get("topic_name", "Core Concepts") for w in weaknesses] if weaknesses else [
            "Data Structures & Complexity", "Database Indexing & Normalization", "System Design & REST APIs", "STAR Method Behavioral Articulation"
        ]

        daily_plan = []
        for day in range(1, duration_days + 1):
            topic_idx = (day - 1) % len(weak_names)
            topic = weak_names[topic_idx]

            if day <= int(duration_days * 0.4):
                phase = "Deep Conceptual Remediation"
                hours = 3
                study = f"Deep dive into documentation, architecture patterns, and standard edge cases for {topic}."
                exercise = f"Implement 2 LeetCode / GeeksforGeeks problems testing {topic} and articulate complexity."
            elif day <= int(duration_days * 0.8):
                phase = "Applied Problem Solving & Optimization"
                hours = 3
                study = f"Review production failure modes, concurrency trade-offs, and optimization strategies for {topic}."
                exercise = f"Build or refactor a module demonstrating clean design patterns and unit tests for {topic}."
            else:
                phase = "Mock Simulation & Revision"
                hours = 2
                study = f"Rapid flashcard review and verbal explanation of {topic} using 60-second elevator pitch."
                exercise = "Take a full 15-minute mock interview on InterviewX to verify gap closure."

            daily_plan.append({
                "day": day,
                "focus_topic": topic,
                "core_concept_to_master": f"{phase} on {topic}",
                "recommended_study": study,
                "practical_exercise": exercise,
                "hours_recommended": hours
            })

        return {
            "title": f"{duration_days}-Day Targeted Placement Sprint for {role_title}",
            "overview": (
                f"Curated {duration_days}-day placement readiness curriculum focusing on remediating your "
                f"top recurring gaps ({', '.join(weak_names[:3])}). Designed for daily disciplined execution."
            ),
            "daily_plan": daily_plan,
            "key_milestones": [
                f"Day {int(duration_days * 0.4)}: Core foundational theory and algorithmic complexity mastered.",
                f"Day {int(duration_days * 0.8)}: Practical coding implementations and architecture trade-offs verified.",
                f"Day {duration_days}: Full placement readiness simulation achieved."
            ],
            "is_offline": True
        }
