# **AI-Powered Content Analysis Feature**

## **Background**

We are building an AI-powered feature that analyzes content of Instagram/TikTok creators and produces structured insights.

The feature relies on existing integrations and will be expanded into a scalable, production-ready AI pipeline.

Sample of the content/creator: [https://www.tiktok.com/@gabriellarenees/video/7566704196913827127?is\_from\_webapp=1\&sender\_device=pc\&web\_id=7593428963696625164](https://www.tiktok.com/@gabriellarenees/video/7566704196913827127?is_from_webapp=1&sender_device=pc&web_id=7593428963696625164)

Imagine that we have to analyse content of the provided creator:

# **Content Analysis Requirements**

## **1\. General Requirements**

1. The system **must analyze both visual and textual content** for each campaign.

2. Analysis results **must be aggregated across all analyzed posts** and reported as percentages.

3. Each category **must return a safety score (0–100%)** and a corresponding **status**.

4. Status values must be standardized:

   * **Safe**

   * **Warning**

   * **Unsafe** (reserved for future use)

---

## **2\. Visual Safety Analysis Requirements**

### **2.1 Analyzed Categories**

The system must evaluate visual content for the following categories:

* Adult Content

* Violence / Weapons

* Racy Content

* Medical / Gore

* Spoof / Fake Content

### **2.2 Scoring & Status Logic**

* Each category must return a **safety percentage**.

* Status assignment rules:

  * **Safe:** ≥ 90%

  * **Warning:** 70% – 89%

  * **Unsafe:** \< 70%

### **2.3 Acceptance Criteria**

* All visual categories with scores ≥ 90% must be marked **Safe**.

* The system must flag **Spoof / Fake content** if the score drops below 90%, even if no other visual risks are present.

* Visual analysis must not block processing if one category fails; partial results must still be returned.

---

## **3\. Text Safety Analysis Requirements**

### **3.1 Analyzed Categories**

The system must evaluate textual content for the following categories:

* Profanity

* Hate Speech

* Misinformation

* Brand Mentions

* Disclosure Compliance

* Political Content

### **3.2 Scoring & Status Logic**

* Each category must return a **safety percentage**.

* Status assignment rules:

  * **Safe:** ≥ 85%

  * **Warning:** 70% – 84%

  * **Unsafe:** \< 70%

### **3.3 Acceptance Criteria**

* Hate Speech and Violence-related categories must always use the **strictest thresholds**.

* Brand Mentions and Disclosure Compliance must:

  * Trigger **Warning** status below 85%

  * Include a short explanation or recommendation

* Political Content must be labeled but must not block campaign approval unless \< 70%.

---

## **4\. Aggregation & Reporting Requirements**

1. The system must calculate:

   * Per-category scores

   * Overall Visual Safety Score

   * Overall Text Safety Score

2. Overall scores must be calculated as a **weighted average**, with higher weight for:

   * Adult Content

   * Violence / Hate Speech

   * Misinformation

3. The system must return a **human-readable summary** and a **structured JSON output**.

---

## **Core AI Pipeline**

The system should follow this flow:

1. **Content ingestion**  
   * Fetch or scrape campaign content via AWS Amplify (assume access exists).  
   * Content may include video, audio, images, and text metadata.  
2. **Audio transcription**  
   * Extract audio from video when needed.  
   * Generate transcripts using AssemblyAI Streaming Speech-to-Text:  
     [https://www.assemblyai.com/products/streaming-speech-to-text](https://www.assemblyai.com/products/streaming-speech-to-text)  
3. **Content & visual analysis**  
   * Analyze images, video frames, and/or text for restricted or sensitive content using Sightengine:  
     [https://sightengine.com/](https://sightengine.com/)  
4. **AI summary**  
   * Generate a concise, human-readable summary of:  
     * The content meaning  
     * The transcript  
     * Detected risks or flags  
   * Use Claude AI for summarization.

---

# 

# **Task** 

## **Objective**

Demonstrate your ability to design and implement AI integrations in a production backend environment.

---

## **What You Need to Deliver**

### **1\. System Design**

Provide a high-level architecture that explains:

* Backend services (Python, AWS)  
* REST API structure  
* Data flow between services  
* Where each AI tool is used  
* Basic error handling and retries

You may include a diagram (optional but encouraged).

---

### **2\. Data Pipeline Definition**

Define:

* Input format  
* Transcript structure  
* Moderation results structure  
* Final API response returned to the frontend

Include example JSON payloads and explain how partial failures are handled.

---

### **3\. Implementation (Required)**

Implement **one** of the following in Python:

* Audio transcription service using AssemblyAI  
  **OR**  
* Content moderation service using Sightengine  
  **OR**  
* AI summarization service using Claude AI

Requirements:

* Clean, modular Python code  
* Environment-based configuration  
* Basic error handling  
* README explaining how to run the code

---

### **4\. Short Optimization Notes**

Briefly explain:

* How you would reduce latency  
* How you would control AI-related costs  
* What you would improve next

---

## **Time Expectation**

**4–6 hours**

---

## **Evaluation Criteria**

* Code quality and structure  
* Practical AI integration skills  
* Clear system thinking  
* Production-readiness mindset

