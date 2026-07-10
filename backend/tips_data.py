"""
tips_data.py
------------
Tiered advice for Content, Fluency, Pronunciation, now including a
"pre_practice" plan per tier - what to practice BEFORE attempting
graded Repeat Sentence practice, with duration/frequency and
real-world practice scenarios.
"""

CONTENT_TIPS = {
    "excellent": {
        "score_range": [
            75,
            90
        ],
        "headline": "Strong content accuracy",
        "tips": [
            "You're capturing almost all the words correctly - keep listening for the exact wording, not just the general meaning.",
            "Watch out for small function words (a, the, to, of) - these are easy to drop even when you understand the sentence fully.",
            "Try slightly longer or harder sentences to keep pushing this skill further."
        ],
        "pre_practice": {
            "activity_name": "Maintenance: longer-sentence memory drills",
            "duration_per_session": "10 minutes",
            "recommended_frequency": "2-3 times per week",
            "how_to": [
                "Listen to 18-22 word sentences (news headlines work well) once, then repeat from memory.",
                "Check your accuracy against the original text afterward."
            ],
            "real_world_practice": [
                "Summarize a short podcast segment aloud right after listening, without notes.",
                "Repeat back voicemail messages or announcements word-for-word as a daily habit."
            ]
        }
    },
    "good": {
        "score_range": [
            55,
            74
        ],
        "headline": "Good grasp, some words slipping through",
        "tips": [
            "Focus on keywords first (nouns, verbs, numbers) - these carry the most scoring weight if you can't catch everything.",
            "If you miss a word, keep going rather than stopping - a partial, fluent sentence scores better than a broken, complete one.",
            "Practice 'chunking' - break the sentence into 2-3 word groups mentally as you listen, instead of trying to hold the whole sentence at once."
        ],
        "pre_practice": {
            "activity_name": "Chunking drills",
            "duration_per_session": "10-15 minutes",
            "recommended_frequency": "4-5 times per week for 1 week",
            "how_to": [
                "Take 10-12 word sentences and mentally split them into 3-word chunks while listening.",
                "Repeat chunk by chunk first, then attempt the full sentence in one go.",
                "Gradually increase sentence length as chunks start to blend naturally."
            ],
            "real_world_practice": [
                "Listen to a friend or video giving directions, then repeat the directions back immediately.",
                "Practice recalling grocery lists or short instructions someone reads aloud to you."
            ]
        }
    },
    "needs_improvement": {
        "score_range": [
            35,
            54
        ],
        "headline": "Content accuracy needs focused practice",
        "tips": [
            "Preserve word order even if you can't remember every word - order matters for scoring, not just word count.",
            "Repeating even 50% of the sentence accurately is better than staying silent or guessing randomly.",
            "Try shadowing practice: listen to a sentence and immediately repeat it to build short-term audio memory."
        ],
        "pre_practice": {
            "activity_name": "Short-term auditory memory building",
            "duration_per_session": "15-20 minutes",
            "recommended_frequency": "Daily for 1-2 weeks before retrying timed practice",
            "how_to": [
                "Start with 5-7 word sentences. Listen once, wait 2 seconds, then repeat.",
                "Only move to 8-10 word sentences once you can repeat short ones with 90%+ accuracy.",
                "Use a notes app to track your daily accuracy so you can see progress."
            ],
            "real_world_practice": [
                "Ask someone to read you a short sentence and repeat it back immediately, several times a day.",
                "Practice with voice-memo apps: record a sentence, play it once, try to repeat, then check.",
                "Use simple language-learning apps with 'listen and repeat' drills for 10 minutes daily."
            ]
        }
    },
    "poor": {
        "score_range": [
            0,
            34
        ],
        "headline": "Let's build up your listening-to-speech memory",
        "tips": [
            "Start with shorter, easier sentences (5-8 words) to build confidence before moving to longer ones.",
            "Practice active listening drills daily: listen to a short sentence, pause, then say it back immediately without looking at text.",
            "Don't worry about perfect grammar - say whatever words you remember, in the order you heard them."
        ],
        "pre_practice": {
            "activity_name": "Foundational listen-and-repeat training",
            "duration_per_session": "20 minutes",
            "recommended_frequency": "Daily for 2-3 weeks before attempting graded practice",
            "how_to": [
                "Begin with 3-5 word phrases only (e.g. 'close the door please').",
                "Listen, repeat immediately, then listen again to self-check.",
                "Increase to 6-8 words only once 3-5 word phrases feel easy and automatic.",
                "Avoid timing yourself at this stage - accuracy first, speed later."
            ],
            "real_world_practice": [
                "Repeat simple phrases from children's audiobooks or beginner-level podcasts.",
                "Practice with a language partner (free apps like Tandem/HelloTalk) doing simple 'say it back' exercises for 10 minutes.",
                "Watch short videos with subtitles, pause after each sentence, and repeat it aloud before continuing."
            ]
        }
    }
}

FLUENCY_TIPS = {
    "excellent": {
        "score_range": [
            75,
            90
        ],
        "headline": "Natural, smooth delivery",
        "tips": [
            "Great pacing - keep this consistent even on longer or unfamiliar sentences.",
            "Make sure you're not just fast, but evenly paced - scoring rewards steady rhythm over raw speed."
        ],
        "pre_practice": {
            "activity_name": "Maintenance: pace consistency drills",
            "duration_per_session": "10 minutes",
            "recommended_frequency": "2-3 times per week",
            "how_to": [
                "Read a paragraph aloud at a fixed pace using a metronome app or steady background beat.",
                "Record yourself and check your pace stays even from start to finish, not rushing at the end."
            ],
            "real_world_practice": [
                "Practice giving a 1-minute impromptu talk on a random topic, keeping a steady rhythm throughout.",
                "Join a public-speaking group to practice consistent pacing under light pressure."
            ]
        }
    },
    "good": {
        "score_range": [
            55,
            74
        ],
        "headline": "Decent flow, minor hesitations",
        "tips": [
            "Start speaking within 1 second of the beep - delayed starts cost fluency points even if the content is correct.",
            "Avoid long pauses mid-sentence to 'remember' a word - keep momentum, even if you substitute a word you're unsure of.",
            "Practice reading sentences aloud daily at a natural conversational pace to build muscle memory."
        ],
        "pre_practice": {
            "activity_name": "Quick-start speaking drills",
            "duration_per_session": "10-15 minutes",
            "recommended_frequency": "4-5 times per week for 1 week",
            "how_to": [
                "Set a timer/beep sound, then practice starting to speak within 1 second every time it goes off.",
                "Read sentences aloud without stopping, even if you stumble on a word - keep moving forward.",
                "Time yourself reading a paragraph 3 times, aiming for the same, steady duration each time."
            ],
            "real_world_practice": [
                "Practice answering random questions out loud immediately, without planning your answer first.",
                "Try 'think aloud' narration - describe what you're doing while cooking or walking, without pausing to search for perfect words."
            ]
        }
    },
    "needs_improvement": {
        "score_range": [
            35,
            54
        ],
        "headline": "Pace needs work - too rushed or too hesitant",
        "tips": [
            "If you're rushing: slow down slightly and focus on clear word boundaries - speed doesn't help if words blur together.",
            "If you're hesitating: don't wait for the 'perfect' word - substitute or skip and keep moving forward.",
            "Record yourself and listen back - most people are surprised by how many pauses they don't notice while speaking."
        ],
        "pre_practice": {
            "activity_name": "Shadowing practice for rhythm",
            "duration_per_session": "15-20 minutes",
            "recommended_frequency": "Daily for 1-2 weeks before retrying timed practice",
            "how_to": [
                "Pick a short audio clip (news anchor or podcast, 30-60 seconds).",
                "Play it and speak along simultaneously, matching their rhythm and pace as closely as possible.",
                "Repeat the same clip 3-4 times until your rhythm starts to match naturally."
            ],
            "real_world_practice": [
                "Shadow along with YouTube videos or podcasts in short 30-second bursts daily.",
                "Read children's books aloud - their simple, rhythmic sentences are excellent for pace practice.",
                "Record a 1-minute voice memo describing your day, then listen back and count your pauses."
            ]
        }
    },
    "poor": {
        "score_range": [
            0,
            34
        ],
        "headline": "Let's work on continuous speech flow",
        "tips": [
            "Practice reading simple sentences aloud every day, focusing only on smoothness - accuracy comes later.",
            "Try the 'echo method': listen to a native speaker's sentence and immediately mimic their rhythm and pacing, not just the words.",
            "Avoid restarting a sentence if you make a mistake - a single wrong word costs less than a restart."
        ],
        "pre_practice": {
            "activity_name": "Foundational flow-building drills",
            "duration_per_session": "20 minutes",
            "recommended_frequency": "Daily for 2-3 weeks before attempting graded practice",
            "how_to": [
                "Read very short, simple sentences aloud (5-6 words) at a slow but unbroken pace.",
                "Focus only on NOT stopping mid-sentence - it's fine to be slow, but keep moving.",
                "Gradually increase sentence length only once you can finish short sentences without a single pause."
            ],
            "real_world_practice": [
                "Read a few sentences from a children's book aloud every day, focusing on smooth delivery over speed.",
                "Practice counting aloud from 1 to 30 at a steady pace daily, as a simple fluency warm-up.",
                "Record yourself introducing yourself in one unbroken breath - repeat until it feels smooth."
            ]
        }
    }
}

PRONUNCIATION_TIPS = {
    "excellent": {
        "score_range": [
            75,
            90
        ],
        "headline": "Clear, confident pronunciation",
        "tips": [
            "Your pronunciation is coming through clearly - keep maintaining steady volume and mic distance for consistency.",
            "Pay attention to word stress in multi-syllable words (e.g. PHOtograph vs phoTOgraphy) to push this even further."
        ],
        "pre_practice": {
            "activity_name": "Maintenance: stress and intonation polish",
            "duration_per_session": "10 minutes",
            "recommended_frequency": "2-3 times per week",
            "how_to": [
                "Pick 5 multi-syllable words daily and practice correct stress placement using a dictionary's audio pronunciation.",
                "Record yourself saying them and compare against the reference audio."
            ],
            "real_world_practice": [
                "Watch a short interview clip and mimic the speaker's intonation on a few sentences.",
                "Practice reading news headlines aloud, paying attention to natural word stress."
            ]
        }
    },
    "good": {
        "score_range": [
            55,
            74
        ],
        "headline": "Generally clear, some sounds unclear",
        "tips": [
            "Focus on consonant endings (e.g. -s, -ed, -t) - these are commonly dropped and affect scoring even when the rest of the word is clear.",
            "Keep consistent volume throughout the sentence - many speakers trail off quietly toward the end.",
            "Practice minimal pairs (ship/sheep, bit/beat) to sharpen vowel sounds that are often confused."
        ],
        "pre_practice": {
            "activity_name": "Minimal pairs and word-ending drills",
            "duration_per_session": "15 minutes",
            "recommended_frequency": "4-5 times per week for 1 week",
            "how_to": [
                "Practice 8-10 minimal pairs daily (e.g. ship/sheep, bit/beat, live/leave) - say each pair 5 times, exaggerating the difference.",
                "Read sentences aloud focusing only on clearly finishing word endings (-s, -ed, -t), even if it feels slow at first.",
                "Record and self-check against a native pronunciation sample for the same words."
            ],
            "real_world_practice": [
                "Use a free pronunciation app for 10 minutes daily on words you find tricky.",
                "Order food or ask questions aloud in English during daily errands, focusing on clear word endings.",
                "Read product labels or signs aloud when you're out, practicing clear articulation in real settings."
            ]
        }
    },
    "needs_improvement": {
        "score_range": [
            35,
            54
        ],
        "headline": "Pronunciation clarity needs focused practice",
        "tips": [
            "Slow down slightly - rushing often causes sounds to blend together and lowers clarity, even if you know the words.",
            "Record yourself and compare against a native speaker sample for the same sentence - listen specifically for sounds that differ.",
            "Practice phoneme drills for sounds that don't exist in your native language (e.g. 'th', 'r' vs 'l')."
        ],
        "pre_practice": {
            "activity_name": "Phoneme isolation drills",
            "duration_per_session": "15-20 minutes",
            "recommended_frequency": "Daily for 1-2 weeks before retrying timed practice",
            "how_to": [
                "Identify your 3 hardest sounds (ask a teacher, app, or compare your recordings against native audio).",
                "Practice each sound in isolation first, then in simple words, then in short sentences.",
                "Use a mirror to check tongue and lip position for difficult sounds."
            ],
            "real_world_practice": [
                "Use free phoneme-specific tutorials and practice along, 10 minutes daily.",
                "Join a free conversation exchange call once a week and ask your partner to flag words that were unclear.",
                "Practice tongue twisters targeting your weak sounds for 5 minutes daily as a warm-up."
            ]
        }
    },
    "poor": {
        "score_range": [
            0,
            34
        ],
        "headline": "Let's build pronunciation clarity step by step",
        "tips": [
            "Start with single-word pronunciation drills before moving to full sentences.",
            "Use a mirror or record video of yourself to check mouth and tongue position for difficult sounds.",
            "Slow, deliberate practice beats fast, unclear practice - accuracy first, speed later."
        ],
        "pre_practice": {
            "activity_name": "Foundational phoneme and word-level training",
            "duration_per_session": "20-25 minutes",
            "recommended_frequency": "Daily for 2-3 weeks before attempting graded practice",
            "how_to": [
                "Start with basic vowel and consonant sounds, practiced slowly and individually.",
                "Move to single words once individual sounds feel steady, using a mirror to check mouth position.",
                "Only attempt short phrases (3-4 words) once single words are consistently clear."
            ],
            "real_world_practice": [
                "Use a structured beginner pronunciation app daily for 15-20 minutes.",
                "Practice saying your name, address, and basic personal details clearly - useful both for confidence and real-life situations.",
                "Record short voice memos daily saying 5 simple words, and track improvement week over week."
            ]
        }
    }
}

GENERAL_STRATEGY_TIPS = [
    "Scoring priority for Repeat Sentence: Content > Fluency > Pronunciation - if you have to choose, prioritize saying the right words.",
    "Partial, confident repetition beats silence - always say something, even if incomplete.",
    "You only hear the sentence once - use the first half-second to mentally anchor the sentence's topic before it fully plays.",
    "Practice a little every day rather than long sessions occasionally - short-term audio memory improves fastest with frequent repetition.",
    "If you're weak in multiple areas at once, focus on ONE skill's pre-practice plan at a time rather than all three together - it's more effective and less overwhelming."
]


def _pick_tier(tiers: dict, score: float) -> dict:
    for tier_data in tiers.values():
        low, high = tier_data["score_range"]
        if low <= score <= high:
            return tier_data
    return list(tiers.values())[0]


def get_tips_for_score(content_score: float, fluency_score: float, pronunciation_score: float) -> dict:
    """
    Returns tiered tips (including a pre_practice plan) for all three
    categories, plus general strategy reminders. Dropped straight into
    the JSON response returned by /api/score.
    """
    return {
        "content": _pick_tier(CONTENT_TIPS, content_score),
        "fluency": _pick_tier(FLUENCY_TIPS, fluency_score),
        "pronunciation": _pick_tier(PRONUNCIATION_TIPS, pronunciation_score),
        "general": GENERAL_STRATEGY_TIPS,
    }