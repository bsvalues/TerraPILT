/**
 * AI Assistant functionality for PILT Dashboard
 * This module provides AI-powered features for data analysis and insights
 */

class AIAssistant {
    constructor(apiKey = null) {
        this.apiKey = apiKey;
        this.isAvailable = !!apiKey;
        this.apiEndpoint = 'https://api.openai.com/v1/chat/completions';
        this.model = 'gpt-3.5-turbo';
        this.messageHistory = [];
        this.systemPrompt = `You are an AI assistant for a Payment in Lieu of Taxes (PILT) Dashboard.
Your role is to help analysts understand PILT data, discover insights, and make better decisions.
Focus on providing clear, concise explanations about PILT calculations, trends, and anomalies.
Always respond in a professional tone, focusing on accuracy and clarity.
Never make up data - only analyze the information provided to you.
Provide suggestions for further analysis when appropriate.`;
    }

    /**
     * Set the OpenAI API key
     * @param {string} apiKey - The OpenAI API key
     */
    setApiKey(apiKey) {
        this.apiKey = apiKey;
        this.isAvailable = !!apiKey;
        return this.isAvailable;
    }

    /**
     * Clear the message history
     */
    clearHistory() {
        this.messageHistory = [];
    }

    /**
     * Add a message to the history
     * @param {string} role - The role of the message sender ('user', 'assistant', or 'system')
     * @param {string} content - The message content
     */
    addMessage(role, content) {
        this.messageHistory.push({ role, content });
    }

    /**
     * Get the current PILT data and format it for analysis
     * @param {Array} piltData - The PILT data to analyze
     * @returns {string} - A text representation of the data
     */
    formatDataForAnalysis(piltData) {
        if (!piltData || !piltData.length) {
            return "No PILT data is currently available for analysis.";
        }

        let dataText = "Current PILT Data:\n";
        
        // Add headers
        dataText += "District | Assessed Value | Levy Rate | Base PILT | Deduction | PILT Due\n";
        dataText += "---------|----------------|-----------|-----------|-----------|----------\n";
        
        // Add data rows
        piltData.forEach(district => {
            dataText += `${district.district} | ${district.assessedValue} | ${district.levyRate} | ${district.basePILT} | ${district.deduction} | ${district.piltDue}\n`;
        });
        
        return dataText;
    }

    /**
     * Get insights about the current PILT data
     * @param {Array} piltData - The PILT data to analyze
     * @returns {Promise<string>} - The insights text
     */
    async getDataInsights(piltData) {
        if (!this.isAvailable) {
            return "AI insights are not available. Please provide an OpenAI API key in the settings.";
        }

        try {
            const dataText = this.formatDataForAnalysis(piltData);
            
            const messages = [
                { role: "system", content: this.systemPrompt },
                { role: "user", content: `Please analyze this PILT data and provide key insights:\n\n${dataText}\n\nFocus on interesting patterns, outliers, or significant values. Provide 3-5 brief but specific insights.` }
            ];
            
            const response = await this.callOpenAI(messages);
            return response;
        } catch (error) {
            console.error("Error getting AI insights:", error);
            return `Error generating insights: ${error.message}`;
        }
    }

    /**
     * Get recommendations for what-if scenarios
     * @param {Array} piltData - The current PILT data
     * @returns {Promise<string>} - The recommendations text
     */
    async getWhatIfRecommendations(piltData) {
        if (!this.isAvailable) {
            return "AI recommendations are not available. Please provide an OpenAI API key in the settings.";
        }

        try {
            const dataText = this.formatDataForAnalysis(piltData);
            
            const messages = [
                { role: "system", content: this.systemPrompt },
                { role: "user", content: `Based on this PILT data, suggest 3 interesting "what-if" scenarios that would be valuable to analyze:\n\n${dataText}\n\nFor each scenario, explain why it's interesting and what specific parameters to adjust.` }
            ];
            
            const response = await this.callOpenAI(messages);
            return response;
        } catch (error) {
            console.error("Error getting what-if recommendations:", error);
            return `Error generating recommendations: ${error.message}`;
        }
    }

    /**
     * Explain a PILT calculation in simple terms
     * @param {Object} district - The district data
     * @returns {Promise<string>} - The explanation text
     */
    async explainCalculation(district) {
        if (!this.isAvailable) {
            return "AI explanations are not available. Please provide an OpenAI API key in the settings.";
        }

        try {
            const messages = [
                { role: "system", content: this.systemPrompt },
                { role: "user", content: `Please explain the PILT calculation for this district in simple terms:\n\nDistrict: ${district.district}\nAssessed Value: ${district.assessedValue}\nLevy Rate: ${district.levyRate}\nDeduction: ${district.deduction}\nBase PILT: ${district.basePILT}\nPILT Due: ${district.piltDue}\n\nExplain how we get from the assessed value to the final PILT due.` }
            ];
            
            const response = await this.callOpenAI(messages);
            return response;
        } catch (error) {
            console.error("Error getting calculation explanation:", error);
            return `Error generating explanation: ${error.message}`;
        }
    }

    /**
     * Chat with the AI about PILT data
     * @param {string} userMessage - The user's message
     * @param {Array} piltData - The current PILT data (optional)
     * @returns {Promise<string>} - The AI's response
     */
    async chat(userMessage, piltData = null) {
        if (!this.isAvailable) {
            return "AI chat is not available. Please provide an OpenAI API key in the settings.";
        }

        try {
            // Add data context if provided
            let fullMessage = userMessage;
            if (piltData) {
                const dataText = this.formatDataForAnalysis(piltData);
                fullMessage = `${userMessage}\n\nFor reference, here's the current PILT data:\n${dataText}`;
            }
            
            // Add to history
            this.addMessage('user', fullMessage);
            
            // Construct messages including history
            const messages = [
                { role: "system", content: this.systemPrompt },
                ...this.messageHistory
            ];
            
            const response = await this.callOpenAI(messages);
            
            // Add response to history
            this.addMessage('assistant', response);
            
            return response;
        } catch (error) {
            console.error("Error in AI chat:", error);
            return `Error in chat: ${error.message}`;
        }
    }

    /**
     * Generate a summary report of the PILT data
     * @param {Array} piltData - The PILT data to summarize
     * @returns {Promise<string>} - The summary report text
     */
    async generateSummaryReport(piltData) {
        if (!this.isAvailable) {
            return "AI report generation is not available. Please provide an OpenAI API key in the settings.";
        }

        try {
            const dataText = this.formatDataForAnalysis(piltData);
            
            // Calculate some aggregated values for context
            const totalAssessedValue = piltData.reduce((sum, district) => sum + district.assessedValue, 0);
            const totalPiltDue = piltData.reduce((sum, district) => sum + district.piltDue, 0);
            const avgLevyRate = piltData.reduce((sum, district) => sum + district.levyRate, 0) / piltData.length;
            
            const messages = [
                { role: "system", content: this.systemPrompt },
                { role: "user", content: `Please generate a professional executive summary of this PILT data:\n\n${dataText}\n\nTotal Assessed Value: ${totalAssessedValue}\nAverage Levy Rate: ${avgLevyRate}\nTotal PILT Due: ${totalPiltDue}\n\nInclude key findings, major contributors, and any patterns or outliers. Format it as a professional report with sections.` }
            ];
            
            const response = await this.callOpenAI(messages);
            return response;
        } catch (error) {
            console.error("Error generating summary report:", error);
            return `Error generating report: ${error.message}`;
        }
    }

    /**
     * Call the OpenAI API
     * @param {Array} messages - The messages to send
     * @returns {Promise<string>} - The text response
     */
    async callOpenAI(messages) {
        try {
            // Check for API key
            if (!this.apiKey) {
                throw new Error("No API key provided");
            }
            
            // Prepare request body
            const requestBody = {
                model: this.model,
                messages: messages,
                temperature: 0.7,
                max_tokens: 1000
            };
            
            // Make API call
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.apiKey}`
                },
                body: JSON.stringify(requestBody)
            });
            
            // Handle response
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error?.message || "Unknown API error");
            }
            
            const data = await response.json();
            return data.choices[0].message.content;
        } catch (error) {
            console.error("OpenAI API error:", error);
            throw error;
        }
    }
}

// Create and export a singleton instance
const aiAssistant = new AIAssistant();
window.aiAssistant = aiAssistant;