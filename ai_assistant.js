/**
 * AI Assistant functionality for PILT Dashboard
 * This module provides AI-powered features for data analysis and insights
 */

class AIAssistant {
    constructor(apiKey = null) {
        this.apiKey = apiKey;
        this.messageHistory = [];
        
        // Add initial system message to set context
        this.addMessage('system', 
            'You are an AI assistant for a PILT (Payment in Lieu of Taxes) dashboard. ' +
            'Your role is to help users understand and analyze their PILT data. ' +
            'Respond in a helpful, clear manner with accurate information about PILT calculations, ' +
            'district data, and financial implications. ' +
            'PILT is calculated as (Assessed Value × Levy Rate) - Deduction = PILT Due.'
        );
    }
    
    /**
     * Set the OpenAI API key
     * @param {string} apiKey - The OpenAI API key
     */
    setApiKey(apiKey) {
        this.apiKey = apiKey;
    }
    
    /**
     * Clear the message history
     */
    clearHistory() {
        this.messageHistory = [];
        
        // Re-add the system message
        this.addMessage('system', 
            'You are an AI assistant for a PILT (Payment in Lieu of Taxes) dashboard. ' +
            'Your role is to help users understand and analyze their PILT data. ' +
            'Respond in a helpful, clear manner with accurate information about PILT calculations, ' +
            'district data, and financial implications. ' +
            'PILT is calculated as (Assessed Value × Levy Rate) - Deduction = PILT Due.'
        );
    }
    
    /**
     * Add a message to the history
     * @param {string} role - The role of the message sender ('user', 'assistant', or 'system')
     * @param {string} content - The message content
     */
    addMessage(role, content) {
        this.messageHistory.push({
            role: role,
            content: content
        });
        
        // Limit history to 20 messages for performance
        if (this.messageHistory.length > 20) {
            // Remove the oldest user/assistant message (but keep the system message)
            const systemMessages = this.messageHistory.filter(msg => msg.role === 'system');
            const otherMessages = this.messageHistory.filter(msg => msg.role !== 'system');
            otherMessages.shift(); // Remove oldest non-system message
            this.messageHistory = [...systemMessages, ...otherMessages];
        }
    }
    
    /**
     * Get the current PILT data and format it for analysis
     * @param {Array} piltData - The PILT data to analyze
     * @returns {string} - A text representation of the data
     */
    formatDataForAnalysis(piltData) {
        if (!piltData || piltData.length === 0) {
            return "No PILT data available.";
        }
        
        let totalAssessedValue = 0;
        let totalBasePILT = 0;
        let totalDeduction = 0;
        let totalPILTDue = 0;
        let avgLevyRate = 0;
        
        const dataText = piltData.map(district => {
            totalAssessedValue += district.assessedValue || 0;
            totalBasePILT += district.basePILT || 0;
            totalDeduction += district.deduction || 0;
            totalPILTDue += district.piltDue || 0;
            avgLevyRate += district.levyRate || 0;
            
            return `District: ${district.district}
Assessed Value: $${(district.assessedValue || 0).toLocaleString('en-US', {maximumFractionDigits: 2})}
Levy Rate: ${(district.levyRate || 0).toFixed(6)}
Base PILT: $${(district.basePILT || 0).toLocaleString('en-US', {maximumFractionDigits: 2})}
Deduction: $${(district.deduction || 0).toLocaleString('en-US', {maximumFractionDigits: 2})}
PILT Due: $${(district.piltDue || 0).toLocaleString('en-US', {maximumFractionDigits: 2})}
`;
        }).join('\n');
        
        avgLevyRate = avgLevyRate / piltData.length;
        
        const summary = `
Summary:
Total Districts: ${piltData.length}
Total Assessed Value: $${totalAssessedValue.toLocaleString('en-US', {maximumFractionDigits: 2})}
Average Levy Rate: ${avgLevyRate.toFixed(6)}
Total Base PILT: $${totalBasePILT.toLocaleString('en-US', {maximumFractionDigits: 2})}
Total Deductions: $${totalDeduction.toLocaleString('en-US', {maximumFractionDigits: 2})}
Total PILT Due: $${totalPILTDue.toLocaleString('en-US', {maximumFractionDigits: 2})}
`;
        
        return dataText + summary;
    }
    
    /**
     * Get insights about the current PILT data
     * @param {Array} piltData - The PILT data to analyze
     * @returns {Promise<string>} - The insights text
     */
    async getDataInsights(piltData) {
        if (!this.apiKey) {
            throw new Error("API key not set. Please configure your OpenAI API key in Settings.");
        }
        
        // Format data for analysis
        const dataText = this.formatDataForAnalysis(piltData);
        
        // Create prompt
        const prompt = `
Analyze the following PILT (Payment in Lieu of Taxes) data and provide meaningful insights:

${dataText}

Please provide insights including:
1. Districts with highest and lowest PILT due
2. Analysis of levy rates across districts
3. Impact of deductions on final PILT amounts
4. Any anomalies or interesting patterns in the data
5. Distribution of tax burden across districts

Make your insights clear, concise, and meaningful for financial planning.
`;
        
        this.addMessage('user', prompt);
        
        // Call API
        const response = await this.callOpenAI(this.messageHistory);
        
        // Store response
        this.addMessage('assistant', response);
        
        return response;
    }
    
    /**
     * Get recommendations for what-if scenarios
     * @param {Array} piltData - The current PILT data
     * @returns {Promise<string>} - The recommendations text
     */
    async getWhatIfRecommendations(piltData) {
        if (!this.apiKey) {
            throw new Error("API key not set. Please configure your OpenAI API key in Settings.");
        }
        
        // Format data for analysis
        const dataText = this.formatDataForAnalysis(piltData);
        
        // Create prompt
        const prompt = `
Based on the following PILT (Payment in Lieu of Taxes) data, suggest 3-5 "what-if" scenarios that would be valuable to analyze:

${dataText}

For each scenario:
1. Describe the specific parameter changes (e.g., increase levy rate by X% for specific districts)
2. Explain why analyzing this scenario would be valuable
3. Predict the potential impact on total PILT revenue

Make your suggestions practical and relevant for financial planning and policy decisions.
`;
        
        this.addMessage('user', prompt);
        
        // Call API
        const response = await this.callOpenAI(this.messageHistory);
        
        // Store response
        this.addMessage('assistant', response);
        
        return response;
    }
    
    /**
     * Explain a PILT calculation in simple terms
     * @param {Object} district - The district data
     * @returns {Promise<string>} - The explanation text
     */
    async explainCalculation(district) {
        if (!this.apiKey) {
            throw new Error("API key not set. Please configure your OpenAI API key in Settings.");
        }
        
        if (!district) {
            throw new Error("No district data provided.");
        }
        
        // Create prompt
        const prompt = `
Explain the PILT calculation for the following district in simple, clear terms:

District: ${district.district}
Assessed Value: $${(district.assessedValue || 0).toLocaleString('en-US', {maximumFractionDigits: 2})}
Levy Rate: ${(district.levyRate || 0).toFixed(6)}
Base PILT: $${(district.basePILT || 0).toLocaleString('en-US', {maximumFractionDigits: 2})}
Deduction: $${(district.deduction || 0).toLocaleString('en-US', {maximumFractionDigits: 2})}
PILT Due: $${(district.piltDue || 0).toLocaleString('en-US', {maximumFractionDigits: 2})}

Show the step-by-step calculation and explain each component in terms that a non-technical person would understand. Include a brief explanation of what PILT is and why it matters.
`;
        
        this.addMessage('user', prompt);
        
        // Call API
        const response = await this.callOpenAI(this.messageHistory);
        
        // Store response
        this.addMessage('assistant', response);
        
        return response;
    }
    
    /**
     * Chat with the AI about PILT data
     * @param {string} userMessage - The user's message
     * @param {Array} piltData - The current PILT data (optional)
     * @returns {Promise<string>} - The AI's response
     */
    async chat(userMessage, piltData = null) {
        if (!this.apiKey) {
            throw new Error("API key not set. Please configure your OpenAI API key in Settings.");
        }
        
        // If we have PILT data, add it as context
        if (piltData && piltData.length > 0) {
            // Only add data if the message history is short
            if (this.messageHistory.length <= 3) {
                const dataText = this.formatDataForAnalysis(piltData);
                this.addMessage('system', `Current PILT data:\n${dataText}`);
            }
        }
        
        // Add user message
        this.addMessage('user', userMessage);
        
        // Call API
        const response = await this.callOpenAI(this.messageHistory);
        
        // Store response
        this.addMessage('assistant', response);
        
        return response;
    }
    
    /**
     * Generate a summary report of the PILT data
     * @param {Array} piltData - The PILT data to summarize
     * @returns {Promise<string>} - The summary report text
     */
    async generateSummaryReport(piltData) {
        if (!this.apiKey) {
            throw new Error("API key not set. Please configure your OpenAI API key in Settings.");
        }
        
        // Format data for analysis
        const dataText = this.formatDataForAnalysis(piltData);
        
        // Create prompt
        const prompt = `
Generate a comprehensive summary report for the following PILT (Payment in Lieu of Taxes) data:

${dataText}

Your report should include:
1. Executive Summary - Key figures and highlights
2. District-by-District Analysis - Brief assessment of each district's contribution
3. Financial Impact Analysis - How PILT payments affect the county budget
4. Distribution Analysis - How the tax burden is distributed
5. Comparison to Previous Periods (if data available) or to average values
6. Recommendations - Based on the data, what recommendations would you make

Format the report in a professional, clear manner suitable for presentation to county officials.
`;
        
        this.addMessage('user', prompt);
        
        // Call API
        const response = await this.callOpenAI(this.messageHistory);
        
        // Store response
        this.addMessage('assistant', response);
        
        return response;
    }
    
    /**
     * Call the OpenAI API
     * @param {Array} messages - The messages to send
     * @returns {Promise<string>} - The text response
     */
    async callOpenAI(messages) {
        if (!this.apiKey) {
            throw new Error("API key not set. Please configure your OpenAI API key in Settings.");
        }
        
        try {
            const response = await fetch('https://api.openai.com/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.apiKey}`
                },
                body: JSON.stringify({
                    model: 'gpt-3.5-turbo',
                    messages: messages,
                    temperature: 0.7,
                    max_tokens: 1000
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`API error: ${errorData.error?.message || response.statusText}`);
            }
            
            const data = await response.json();
            return data.choices[0].message.content;
        } catch (error) {
            console.error('Error calling OpenAI API:', error);
            throw new Error(`Failed to get AI response: ${error.message}`);
        }
    }
}

// Initialize AI Assistant as a global object
window.aiAssistant = new AIAssistant();

// Try to load API key from localStorage
document.addEventListener('DOMContentLoaded', function() {
    const apiKey = localStorage.getItem('openai_api_key');
    if (apiKey) {
        window.aiAssistant.setApiKey(apiKey);
    }
});