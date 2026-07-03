### **Phase 1: Front Matter & Introduction (Pages 1–4)**

*(No complex astrological APIs required here; relies on user input variables like Name, Date of Birth, and Place of Birth).*

### **Phase 2: Core Cosmic Personality & The Soul Mirror (Pages 5–9)**

**Goal:** To generate the D1 birth chart, analyze the core emotional personality, and assess the romantic energy (5th House) and Venus.

* **AllPlanetRasiSigns** & **AllHouseRasiSigns**:  
  * *Target:* Page 5 (Technical Astral Map \- D1 Birth Chart).  
  * *Use:* Renders the visual D1 chart and sets the foundation for the entire report.  
* **LagnaSignName** & **LordOfHouse** (Targeting 1st House):  
  * *Target:* Page 6 (1st House Energy – Nature & Your Core Essence).  
  * *Use:* Determines the Ascendant sign and its ruling planet to describe the user's outer emotional shield.  
* **MoonSignName**:  
  * *Target:* Page 7 (Moon Sign – Your Emotional Sanctuary).  
  * *Use:* Drives the prose detailing their deepest subconscious needs and emotional vulnerabilities.  
* **PlanetsInHouseBasedOnSign** & **LordOfHouse** (Targeting 5th House):  
  * *Target:* Page 8 (5th House Energy – The Spark of Friendship).  
  * *Use:* Identifies planets influencing the house of romance and creative affection.  
* **PlanetsInConjunction** (Targeting Venus), **PlanetCombinedRelationshipWithPlanet**, & **IsPlanetCombust**:  
  * *Target:* Page 9 (The Language of Venus Conjunctions).  
  * *Use:* Checks if Venus is burned by the Sun (combust) or flavored by conjunct planets to write the "Love Language" section.

### **Phase 3: The Marriage Gateway & Divisional Deep-Dives (Pages 10–15)**

**Goal:** To analyze the 7th house, the spouse's characteristics, and calculate the D9 (Navamsa) and D30 (Trimshamsha) charts.

* **AllPlanetNavamshaSign** & **AllPlanetTrimshamshaSign**:  
  * *Target:* Page 10 (Technical Divisional Charts Map).  
  * *Use:* Renders the D9 and D30 charts for the backend UI.  
* **LordOfHouse** (Targeting 7th House) & **PlanetsInHouseBasedOnSign**:  
  * *Target:* Pages 11 & 12 (7th House Energy & Spouse Nature).  
  * *Use:* Identifies the marriage lord and its Rasi to generate the physical/psychological profile of the destined spouse.  
* **HouseNavamshaD9Sign**:  
  * *Target:* Pages 13 & 14 (The D9 Navamsa Revelation).  
  * *Use:* Compares the 7th house in the D1 chart to the D9 chart to explain how the marriage evolves over time.  
* **HouseTrimshamshaD30Sign**:  
  * *Target:* Page 15 (The D30 Trimsamsha Analysis).  
  * *Use:* Maps the psychological shadow elements and loyalty challenges in the relationship.

### **Phase 4: Karmic Loops & Cosmic Red Flags (Pages 16–19)**

**Goal:** To identify relationship blockages, toxic traits to avoid, and classical afflictions.

* **IsPlanetAfflicted**:  
  * *Target:* Page 16 (Recurring Relationship Patterns & Karmic Loops).  
  * *Use:* Checks if the 7th Lord or Venus is debilitated or aspected by malefics, feeding into the "Karmic Loops" narrative.  
* **KujaDosaScore**:  
  * *Target:* Page 17 (Planetary Blockages).  
  * *Use:* Calculates the severity of Mars' influence (Manglik Dosha) to warn about stubbornness or defensive walls.  
* **MaleficPlanetListForLagna** & **BeneficPlanetList**:  
  * *Target:* Page 18 (Cosmic Red Flags).  
  * *Use:* Identifies which planets bring grace and which cause friction, tailoring the red flags the user must avoid in a partner.  
* **IsFireSign**, **IsWaterSign**, **IsEarthSign**, **IsAirSign**:  
  * *Target:* Page 19 (Relationship Risk Matrix).  
  * *Use:* Performs elemental matching checks to summarize the core relationship risks.

### **Phase 5: The Sacred Timeline & Planetary Seasons (Pages 20–22)**

**Goal:** To map the timing of romantic events using the Vimshottari Dasha system.

* **DasaAtRange**:  
  * *Target:* Page 20 & 21 (Cosmic Seasons & 3-Year Advanced Dasha Forecast).  
  * *Use:* Fetches the sequence of Mahadashas and Antardashas over the next 3 years to create the year-by-year love forecast.  
* **DasaAtTime** & **DasaForNow**:  
  * *Target:* Page 22 (Precision Sub-Minor Forecast).  
  * *Use:* Zooms in on the current month's Pratyantar Dasha to give immediate, actionable romantic guidance.

### **Phase 6: Practical Alignments, Remedies & Synthesis (Pages 23–25)**

**Goal:** To provide text-generation helpers that ensure the AI uses traditional Vedic terminology and crafts personalized remedies.

* **GetPlanetTags**, **GetHouseTags**, & **GetSignTags**:  
  * *Target:* Pages 23 & 24 (Mantras & Practical Remedies).  
  * *Use:* Feeds traditional keywords (e.g., "fiery," "tamasic," "royal") into the LLM prompt to ensure the generated remedies and affirmations match the exact flavor of the user's afflicted planets.  
* **GetDasaInfoForAscendant**:  
  * *Target:* Page 25 (Final Heart Synthesis).  
  * *Use:* Provides overarching rules about how the current Dasha lord behaves for their specific Ascendant, ensuring the closing advice is astrologically sound and highly personalized.