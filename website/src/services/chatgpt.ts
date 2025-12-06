/**
 * ChatGPT API Service
 * Handles communication with OpenAI API for stylist chat functionality
 */

const OPENAI_API_KEY = import.meta.env.VITE_OPENAI_API_KEY || '';
const OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions';

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  imageUrl?: string; // For user messages with images
}

export interface ChatResponse {
  message: string;
  error?: string;
}

export interface ItemAnalysis {
  category?: string;
  color?: string;
  style?: string;
  material?: string;
  pattern?: string;
  season?: string;
  occasion?: string;
  description?: string;
}

/**
 * Convert image file to base64 data URL
 */
export async function imageToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

/**
 * Analyze clothing item from image
 * Returns structured analysis of the item's features
 */
export async function analyzeClothingItem(imageFile: File): Promise<ItemAnalysis> {
  if (!OPENAI_API_KEY) {
    throw new Error('OpenAI API key is not configured.');
  }

  try {
    const imageBase64 = await imageToBase64(imageFile);

    const systemMessage = {
      role: 'system' as const,
      content: `You are a fashion expert. Analyze the clothing item in the image and provide a detailed analysis in JSON format with the following structure:
{
  "category": "ONE of these exact categories: 'shirt', 'pants', 'dress', 'jacket', 'shoes', 'accessories'. Choose the most appropriate single category.",
  "color": "primary color name (e.g., 'black', 'white', 'blue', 'brown', 'green')",
  "style": "style description (e.g., 'casual', 'formal', 'sporty', 'elegant')",
  "material": "fabric type if visible (e.g., 'cotton', 'denim', 'silk', 'wool')",
  "pattern": "pattern type (e.g., 'solid', 'striped', 'floral', 'plaid')",
  "season": "appropriate seasons (e.g., 'spring/summer', 'fall/winter', 'all seasons')",
  "occasion": "suitable occasions (e.g., 'work', 'casual', 'party', 'formal')",
  "description": "brief description of the item"
}

CRITICAL REQUIREMENTS:
1. The "category" field is REQUIRED and must be EXACTLY one of: 'shirt', 'pants', 'dress', 'jacket', 'shoes', 'accessories'. Do not use variations or synonyms.

2. The "color" field is REQUIRED and MUST be the PRIMARY/MAIN color of the OUTERMOST clothing item visible in the image. 
   - IGNORE the color of undergarments, undershirts, collars peeking out, or any inner layers
   - IGNORE the background color
   - FOCUS ONLY on the dominant color of the main garment itself (the sweater, shirt, dress, etc.)
   - If you see a green sweater over a white shirt, the color should be 'green', NOT 'white'
   - If you see a maroon dress, the color should be 'red' (maroon maps to red)
   - Must be a valid color name: 'black', 'white', 'blue', 'brown', 'green', 'red', 'pink', 'purple', 'yellow', 'orange', 'gray', 'beige', 'navy', 'cream', 'khaki'
   - Dark green, olive green, forest green → use 'green'
   - Maroon, burgundy, dark red, wine → use 'red'

3. The "style" field is REQUIRED and must be a valid style description (e.g., 'casual', 'formal', 'sporty', 'elegant', 'bohemian', 'minimalist', 'vintage', 'modern', 'classic', 'edgy', 'feminine', 'masculine', 'chic').

4. ALL THREE fields (category, color, style) MUST be present and valid. Do not use "Unknown" or omit any of these three required fields.`,
    };

    const userMessage = {
      role: 'user' as const,
      content: [
        {
          type: 'text',
          text: 'Please analyze this clothing item and provide the details in JSON format.',
        },
        {
          type: 'image_url',
          image_url: {
            url: imageBase64,
          },
        },
      ],
    };

    const response = await fetch(OPENAI_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: 'gpt-4o',
        messages: [systemMessage, userMessage],
        max_tokens: 500,
        temperature: 0.3, // Lower temperature for more consistent analysis
        response_format: { type: 'json_object' },
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error?.message || 'Failed to analyze image');
    }

    const data = await response.json();
    const analysisText = data.choices[0]?.message?.content || '{}';
    
    try {
      const analysis = JSON.parse(analysisText) as ItemAnalysis;
      
      // Ensure all three required fields are present, use fallback if missing
      const validCategories = ['shirt', 'pants', 'dress', 'jacket', 'shoes', 'accessories'];
      
      // Ensure category exists, if not valid, use 'shirt' as fallback
      if (!analysis.category || analysis.category.trim() === '') {
        analysis.category = 'shirt';
      } else {
        const categoryLower = analysis.category.toLowerCase().trim();
        const isValidCategory = validCategories.some(cat => cat.toLowerCase() === categoryLower);
        if (!isValidCategory) {
          // Choose closest match or default to 'shirt'
          analysis.category = 'shirt';
        }
      }
      
      // Ensure color exists, use 'white' as fallback
      if (!analysis.color || analysis.color.trim() === '') {
        analysis.color = 'white';
      }
      
      // Ensure style exists, use 'casual' as fallback
      if (!analysis.style || analysis.style.trim() === '') {
        analysis.style = 'casual';
      }
      
      return analysis;
    } catch (parseError) {
      // If JSON parsing fails, try to extract information from text
      console.warn('Failed to parse JSON, attempting text extraction');
      const extracted = extractAnalysisFromText(analysisText);
      
      // Ensure all three fields exist with fallbacks
      if (!extracted.category || extracted.category.trim() === '') {
        extracted.category = 'shirt';
      }
      if (!extracted.color || extracted.color.trim() === '') {
        extracted.color = 'white';
      }
      if (!extracted.style || extracted.style.trim() === '') {
        extracted.style = 'casual';
      }
      
      return extracted;
    }
  } catch (error) {
    console.error('Analysis error:', error);
    // Instead of throwing, return fallback values to ensure we always have three tags
    console.warn('Analysis failed, using fallback values');
    return {
      category: 'shirt',
      color: 'white',
      style: 'casual',
      description: 'Analysis failed, using default tags'
    };
  }
}

/**
 * Extract analysis from text if JSON parsing fails
 */
function extractAnalysisFromText(text: string): ItemAnalysis {
  const analysis: ItemAnalysis = {};
  
  // Try to extract common patterns
  const categoryMatch = text.match(/category["\s:]+([^",}\n]+)/i);
  if (categoryMatch) analysis.category = categoryMatch[1].trim();
  
  const colorMatch = text.match(/color["\s:]+([^",}\n]+)/i);
  if (colorMatch) analysis.color = colorMatch[1].trim();
  
  const styleMatch = text.match(/style["\s:]+([^",}\n]+)/i);
  if (styleMatch) analysis.style = styleMatch[1].trim();
  
  // Ensure all three fields exist with fallbacks (never throw error)
  if (!analysis.category || analysis.category.trim() === '') {
    analysis.category = 'shirt';
  }
  if (!analysis.color || analysis.color.trim() === '') {
    analysis.color = 'white';
  }
  if (!analysis.style || analysis.style.trim() === '') {
    analysis.style = 'casual';
  }
  
  return analysis;
}

/**
 * Send a message to ChatGPT API
 * Supports text-only and text + image messages
 */
export async function sendChatMessage(
  messages: ChatMessage[],
  imageFile?: File
): Promise<ChatResponse> {
  if (!OPENAI_API_KEY) {
    return {
      message: '',
      error: 'OpenAI API key is not configured. Please set VITE_OPENAI_API_KEY in your .env file.',
    };
  }

  try {
    // Prepare messages for OpenAI API
    const apiMessages: any[] = messages.map((msg) => {
      if (msg.imageUrl && msg.role === 'user') {
        // For messages with images, we need to use vision API format
        return {
          role: msg.role,
          content: [
            {
              type: 'text',
              text: msg.content || 'What styling advice can you give me about this item?',
            },
            {
              type: 'image_url',
              image_url: {
                url: msg.imageUrl, // base64 data URL
              },
            },
          ],
        };
      }
      return {
        role: msg.role,
        content: msg.content,
      };
    });

    // Add system message for stylist persona
    const systemMessage = {
      role: 'system' as const,
      content: `You are a friendly and approachable AI fashion stylist. Your communication style should be:
- CONVERSATIONAL: Talk like a real person, not a robot. Use natural, casual language.
- BRIEF: Keep responses short and concise (2-3 sentences max). Avoid long paragraphs.
- FRIENDLY: Use emojis occasionally (✨ 👗 💫 🎨 👔) to add warmth, but don't overuse them.
- HELPFUL: Give practical, actionable advice without being overly formal.
- ENTHUSIASTIC: Show genuine interest and excitement about fashion.

When users share clothing items, provide brief, friendly analysis focusing on:
- Category, color, and style
- Quick styling suggestions
- Occasion recommendations

Remember: Keep it short, friendly, and conversational - like chatting with a friend who knows fashion!`,
    };

    const response = await fetch(OPENAI_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: imageFile ? 'gpt-4o' : 'gpt-4o', // Use vision-capable model for images
        messages: [systemMessage, ...apiMessages],
        max_tokens: 150, // Reduced for shorter responses
        temperature: 0.8, // Slightly higher for more natural, friendly responses
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMessage = errorData.error?.message || `API error: ${response.statusText}`;
      
      // Provide user-friendly error messages for common errors
      if (errorMessage.includes('quota') || errorMessage.includes('billing')) {
        throw new Error('You exceeded your current quota, please check your plan and billing details.');
      } else if (errorMessage.includes('rate limit')) {
        throw new Error('Too many requests. Please wait a moment and try again.');
      } else if (errorMessage.includes('invalid_api_key')) {
        throw new Error('Invalid API key. Please check your configuration.');
      } else if (errorMessage.includes('insufficient_quota')) {
        throw new Error('Insufficient quota. Please check your OpenAI account billing.');
      }
      
      throw new Error(errorMessage);
    }

    const data = await response.json();
    const assistantMessage = data.choices[0]?.message?.content || '';

    return {
      message: assistantMessage,
    };
  } catch (error) {
    console.error('ChatGPT API error:', error);
    return {
      message: '',
      error: error instanceof Error ? error.message : 'Failed to get response from stylist',
    };
  }
}
