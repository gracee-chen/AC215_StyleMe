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
    console.error('❌ OpenAI API key is not configured. Please set VITE_OPENAI_API_KEY in your .env file.');
    throw new Error('OpenAI API key is not configured. Please set VITE_OPENAI_API_KEY in your .env file.');
  }

  try {
    console.log('🔍 Starting ChatGPT analysis...');
    const imageBase64 = await imageToBase64(imageFile);

    const systemMessage = {
      role: 'system' as const,
      content: `You are a professional fashion expert analyzing clothing items from images. Your task is to accurately identify the category, color, and style of each item.

OUTPUT FORMAT (JSON only):
{
  "category": "ONE of these exact categories: 'shirt', 'pants', 'dress', 'jacket', 'shoes', 'accessories'",
  "color": "primary color name (e.g., 'black', 'white', 'blue', 'brown', 'green')",
  "style": "style description (e.g., 'casual', 'formal', 'sporty', 'elegant')",
  "material": "fabric type if visible (e.g., 'cotton', 'denim', 'silk', 'wool')",
  "pattern": "pattern type (e.g., 'solid', 'striped', 'floral', 'plaid')",
  "season": "appropriate seasons (e.g., 'spring/summer', 'fall/winter', 'all seasons')",
  "occasion": "suitable occasions (e.g., 'work', 'casual', 'party', 'formal')",
  "description": "brief description of the item"
}

═══════════════════════════════════════════════════════════════════
CATEGORY IDENTIFICATION - FOLLOW THESE RULES IN EXACT ORDER:
═══════════════════════════════════════════════════════════════════

STEP 1: Check for SHOES first (highest priority)
   ✓ Look at the BOTTOM of the image - are there feet, soles, heels, or footwear?
   ✓ Boots (ankle, knee-high, combat, UGG, leather, suede, etc.) → 'shoes'
   ✓ Sneakers, athletic shoes, running shoes → 'shoes'
   ✓ Sandals, flip-flops, slides → 'shoes'
   ✓ Heels, pumps, flats, loafers, oxfords → 'shoes'
   ✓ ANY item worn on the feet → 'shoes'
   ⚠️ CRITICAL: If you see footwear, it is ALWAYS 'shoes', NEVER 'shirt' or 'top'

STEP 2: Check for DRESS (second priority)
   ✓ Look for a ONE-PIECE garment that extends from shoulders/chest down to form a skirt
   ✓ A dress is a SINGLE garment combining top and bottom in one piece
   ✓ If the garment flows from upper body to lower body as one continuous piece → 'dress'
   ✓ Even if it's a short dress, mini dress, or maxi dress → 'dress'
   ⚠️ CRITICAL: If it's a dress, it is NEVER 'shirt' or 'top' - dresses are complete garments

STEP 3: Check for PANTS (CRITICAL - check this BEFORE shirt/top)
   ✓ Trousers, jeans, pants, leggings, shorts → 'pants'
   ✓ Any lower body garment that covers legs (fully or partially) → 'pants'
   ✓ Denim jeans, cargo pants, sweatpants, joggers → 'pants'
   ✓ If you see legs, thighs, or lower body garment → 'pants'
   ⚠️ CRITICAL: If it's pants/jeans/trousers, it is ALWAYS 'pants', NEVER 'shirt' or 'top'

STEP 4: Check for JACKET
   ✓ Outerwear: jackets, coats, blazers, cardigans, sweaters, hoodies → 'jacket'
   ✓ Items typically worn OVER other clothing → 'jacket'
   ✓ If it's a sweater or cardigan worn as outer layer → 'jacket'

STEP 5: Check for SHIRT
   ✓ Tops, shirts, blouses, t-shirts, tank tops, camisoles → 'shirt'
   ✓ Upper body garments that are NOT dresses and NOT outerwear → 'shirt'
   ✓ Only use 'shirt' if it's clearly a top and NOT a dress, NOT shoes, NOT pants

STEP 6: Check for ACCESSORIES
   ✓ Bags, handbags, backpacks, purses → 'accessories'
   ✓ Hats, caps, beanies → 'accessories'
   ✓ Scarves, belts, jewelry, watches → 'accessories'

═══════════════════════════════════════════════════════════════════
COLOR IDENTIFICATION - CRITICAL RULES:
═══════════════════════════════════════════════════════════════════

1. IGNORE these colors (they are NOT the main color):
   ✗ Background colors (white backgrounds, colored backgrounds)
   ✗ Inner layers (white collars, undershirts, inner garments)
   ✗ Small details (buttons, zippers, logos, labels)
   ✗ Accessories worn with the item (belts, jewelry, bags)

2. FOCUS ONLY on the OUTERMOST, DOMINANT color of the MAIN garment:
   ✓ Look at the largest visible area of the item
   ✓ If someone is wearing a green sweater over a white shirt → color is 'green'
   ✓ If someone is wearing a green dress → color is 'green' (NOT white from collar)
   ✓ If you see brown/tan/beige shoes → color is 'brown' or 'beige' (NOT white from background)

3. Color mapping rules:
   • Green shades: mint, olive, forest, sage, emerald, lime, teal, jade → 'green'
   • Brown shades: tan, camel, taupe, chocolate, coffee, caramel, suede, leather → 'brown'
   • Beige shades: nude, sand, cream (light brown tones) → 'beige'
   • Red shades: maroon, burgundy, crimson, wine, cherry, dark red → 'red'
   • Blue shades: navy, dark blue → 'navy'; light blue, sky blue → 'blue'
   • Gray shades: grey, silver → 'gray'
   • White shades: ivory, snow → 'white'

4. Valid color names (use EXACTLY these):
   'black', 'white', 'blue', 'brown', 'green', 'red', 'pink', 'purple', 'yellow', 'orange', 'gray', 'beige', 'navy', 'cream', 'khaki'

═══════════════════════════════════════════════════════════════════
STYLE IDENTIFICATION:
═══════════════════════════════════════════════════════════════════

Choose the most appropriate style from: 'casual', 'formal', 'sporty', 'elegant', 'bohemian', 'minimalist', 'vintage', 'modern', 'classic', 'edgy', 'feminine', 'masculine', 'chic'

═══════════════════════════════════════════════════════════════════
FINAL REQUIREMENTS:
═══════════════════════════════════════════════════════════════════

✓ ALL THREE fields (category, color, style) MUST be present
✓ Category MUST be exactly one of: 'shirt', 'pants', 'dress', 'jacket', 'shoes', 'accessories'
✓ Color MUST be one of the valid color names listed above
✓ Style MUST be one of: 'casual', 'formal', 'sporty', 'elegant', 'bohemian', 'minimalist', 'vintage', 'modern', 'classic', 'edgy', 'feminine', 'masculine', 'chic'
✓ NEVER use "miscellaneous", "unknown", "Unknown", "N/A", "n/a", "other", "Other", or any vague terms
✓ Do NOT omit any required fields
✓ If you cannot determine a value, use the most appropriate option from the valid lists above
✓ Analyze the image carefully and follow the priority order for category identification`,
    };

    const userMessage = {
      role: 'user' as const,
      content: [
        {
          type: 'text',
          text: `Analyze the clothing item in this image. 

IMPORTANT INSTRUCTIONS:
1. Look carefully at the image - identify what type of clothing item this is
2. Follow the category identification rules in EXACT order (shoes → dress → pants → jacket → shirt → accessories)
3. Identify the PRIMARY/MAIN color of the OUTERMOST garment (ignore background, inner layers, small details)
4. Determine the style based on the item's appearance

Return your analysis in JSON format with all required fields.`,
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
      const errorMessage = errorData.error?.message || `HTTP ${response.status}: ${response.statusText}`;
      console.error('❌ ChatGPT API error:', errorMessage, errorData);
      throw new Error(`ChatGPT API error: ${errorMessage}`);
    }

    const data = await response.json();
    const analysisText = data.choices[0]?.message?.content || '{}';
    console.log('📥 ChatGPT raw response:', analysisText);
    
    try {
      const analysis = JSON.parse(analysisText) as ItemAnalysis;
      console.log('✅ Parsed analysis:', analysis);
      
      // Ensure all three required fields are present, use fallback if missing
      const validCategories = ['shirt', 'pants', 'dress', 'jacket', 'shoes', 'accessories'];
      const invalidTerms = ['miscellaneous', 'misc', 'unknown', 'n/a', 'other', 'none', 'unclear', 'uncertain'];
      
      // Ensure category exists, if not valid, try to match using normalizeCategoryForSelect logic
      if (!analysis.category || analysis.category.trim() === '') {
        analysis.category = 'shirt';
      } else {
        const categoryLower = analysis.category.toLowerCase().trim();
        // Check if category is an invalid term
        if (invalidTerms.some(term => categoryLower.includes(term))) {
          analysis.category = 'shirt'; // Default fallback
        } else {
          const isValidCategory = validCategories.some(cat => cat.toLowerCase() === categoryLower);
          if (!isValidCategory) {
            // Try to infer from the category string itself before defaulting
            // Check for shoes first
            if (categoryLower.includes('boot') || categoryLower.includes('sneaker') || 
                categoryLower.includes('sandal') || categoryLower.includes('heel') || 
                categoryLower.includes('flat') || categoryLower.includes('shoe')) {
              analysis.category = 'shoes';
            } else if (categoryLower.includes('dress')) {
              analysis.category = 'dress';
            } else if (categoryLower.includes('pant') || categoryLower.includes('jean') || 
                       categoryLower.includes('trouser')) {
              analysis.category = 'pants';
            } else if (categoryLower.includes('jacket') || categoryLower.includes('coat') || 
                       categoryLower.includes('sweater')) {
              analysis.category = 'jacket';
            } else {
              // Default to 'shirt' only if we can't determine
              analysis.category = 'shirt';
            }
          }
        }
      }
      
      // Ensure color exists, use 'white' as fallback
      if (!analysis.color || analysis.color.trim() === '') {
        analysis.color = 'white';
      } else {
        const colorLower = analysis.color.toLowerCase().trim();
        // Check if color is an invalid term
        if (invalidTerms.some(term => colorLower.includes(term))) {
          analysis.color = 'white'; // Default fallback
        }
      }
      
      // Ensure style exists, use 'casual' as fallback
      const validStyles = ['casual', 'formal', 'sporty', 'elegant', 'bohemian', 'minimalist', 'vintage', 'modern', 'classic', 'edgy', 'feminine', 'masculine', 'chic'];
      if (!analysis.style || analysis.style.trim() === '') {
        analysis.style = 'casual';
      } else {
        const styleLower = analysis.style.toLowerCase().trim();
        // Check if style is an invalid term
        if (invalidTerms.some(term => styleLower.includes(term))) {
          analysis.style = 'casual'; // Default fallback
        } else {
          // Check if style is valid
          const isValidStyle = validStyles.some(s => s.toLowerCase() === styleLower);
          if (!isValidStyle) {
            analysis.style = 'casual'; // Default fallback
          }
        }
      }
      
      console.log('✅ Final analysis result:', analysis);
      return analysis;
    } catch (parseError) {
      // If JSON parsing fails, try to extract information from text
      console.warn('⚠️ Failed to parse JSON, attempting text extraction:', parseError);
      console.warn('Raw response text:', analysisText);
      const extracted = extractAnalysisFromText(analysisText);
      
      // Ensure all three fields exist with fallbacks, with smart inference
      const invalidTerms = ['miscellaneous', 'misc', 'unknown', 'n/a', 'other', 'none', 'unclear', 'uncertain'];
      const validCategories = ['shirt', 'pants', 'dress', 'jacket', 'shoes', 'accessories'];
      const validStyles = ['casual', 'formal', 'sporty', 'elegant', 'bohemian', 'minimalist', 'vintage', 'modern', 'classic', 'edgy', 'feminine', 'masculine', 'chic'];
      
      if (!extracted.category || extracted.category.trim() === '') {
        extracted.category = 'shirt';
      } else {
        // Try to infer category from the text if not a valid category
        const categoryLower = extracted.category.toLowerCase().trim();
        // Check if category is an invalid term
        if (invalidTerms.some(term => categoryLower.includes(term))) {
          extracted.category = 'shirt'; // Default fallback
        } else {
          const isValidCategory = validCategories.some(cat => cat.toLowerCase() === categoryLower);
          
          if (!isValidCategory) {
            // Try to infer from the category string
            if (categoryLower.includes('boot') || categoryLower.includes('sneaker') || 
                categoryLower.includes('sandal') || categoryLower.includes('heel') || 
                categoryLower.includes('flat') || categoryLower.includes('shoe')) {
              extracted.category = 'shoes';
            } else if (categoryLower.includes('dress')) {
              extracted.category = 'dress';
            } else if (categoryLower.includes('pant') || categoryLower.includes('jean') || 
                       categoryLower.includes('trouser')) {
              extracted.category = 'pants';
            } else if (categoryLower.includes('jacket') || categoryLower.includes('coat') || 
                       categoryLower.includes('sweater')) {
              extracted.category = 'jacket';
            } else {
              extracted.category = 'shirt';
            }
          }
        }
      }
      if (!extracted.color || extracted.color.trim() === '') {
        extracted.color = 'white';
      } else {
        const colorLower = extracted.color.toLowerCase().trim();
        // Check if color is an invalid term
        if (invalidTerms.some(term => colorLower.includes(term))) {
          extracted.color = 'white'; // Default fallback
        } else {
          // Try to infer color - check for brown/beige/green before white
          if (colorLower.includes('brown') || colorLower.includes('tan') || 
              colorLower.includes('camel') || colorLower.includes('taupe') ||
              colorLower.includes('suede') || colorLower.includes('leather')) {
            extracted.color = 'brown';
          } else if (colorLower.includes('beige') || colorLower.includes('nude') || 
                     colorLower.includes('sand') || colorLower.includes('cream')) {
            extracted.color = 'beige';
          } else if (colorLower.includes('green') || colorLower.includes('mint') || 
                     colorLower.includes('olive') || colorLower.includes('emerald') ||
                     colorLower.includes('sage') || colorLower.includes('forest')) {
            extracted.color = 'green';
          }
        }
      }
      if (!extracted.style || extracted.style.trim() === '') {
        extracted.style = 'casual';
      } else {
        const styleLower = extracted.style.toLowerCase().trim();
        // Check if style is an invalid term
        if (invalidTerms.some(term => styleLower.includes(term))) {
          extracted.style = 'casual'; // Default fallback
        } else {
          // Check if style is valid
          const isValidStyle = validStyles.some(s => s.toLowerCase() === styleLower);
          if (!isValidStyle) {
            extracted.style = 'casual'; // Default fallback
          }
        }
      }
      
      return extracted;
    }
  } catch (error) {
    console.error('❌ Analysis error:', error);
    // Instead of throwing, return fallback values to ensure we always have three tags
    console.warn('⚠️ Analysis failed, using fallback values. This means ChatGPT API was not called successfully.');
    console.warn('⚠️ Check: 1) Is VITE_OPENAI_API_KEY set in .env? 2) Is the API key valid? 3) Check browser console for network errors.');
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
  
  // Try to extract common patterns - be more flexible with regex
  const categoryMatch = text.match(/category["\s:]+([^",}\n]+)/i) || 
                       text.match(/["']category["']\s*:\s*["']([^"']+)["']/i) ||
                       text.match(/category\s*:\s*([^,\n}]+)/i);
  if (categoryMatch) analysis.category = categoryMatch[1].trim().replace(/["']/g, '');
  
  const colorMatch = text.match(/color["\s:]+([^",}\n]+)/i) ||
                    text.match(/["']color["']\s*:\s*["']([^"']+)["']/i) ||
                    text.match(/color\s*:\s*([^,\n}]+)/i);
  if (colorMatch) analysis.color = colorMatch[1].trim().replace(/["']/g, '');
  
  const styleMatch = text.match(/style["\s:]+([^",}\n]+)/i) ||
                    text.match(/["']style["']\s*:\s*["']([^"']+)["']/i) ||
                    text.match(/style\s*:\s*([^,\n}]+)/i);
  if (styleMatch) analysis.style = styleMatch[1].trim().replace(/["']/g, '');
  
  // Also try to extract from description if category/color not found
  if (!analysis.category && text.toLowerCase().includes('dress')) {
    analysis.category = 'dress';
  }
  if (!analysis.category && (text.toLowerCase().includes('boot') || text.toLowerCase().includes('shoe') || 
                              text.toLowerCase().includes('sneaker') || text.toLowerCase().includes('sandal'))) {
    analysis.category = 'shoes';
  }
  
  // Ensure all three fields exist with fallbacks (never throw error)
  const invalidTerms = ['miscellaneous', 'misc', 'unknown', 'n/a', 'other', 'none', 'unclear', 'uncertain'];
  const validCategories = ['shirt', 'pants', 'dress', 'jacket', 'shoes', 'accessories'];
  const validStyles = ['casual', 'formal', 'sporty', 'elegant', 'bohemian', 'minimalist', 'vintage', 'modern', 'classic', 'edgy', 'feminine', 'masculine', 'chic'];
  
  if (!analysis.category || analysis.category.trim() === '') {
    analysis.category = 'shirt';
  } else {
    // Try to infer category from the text if not a valid category
    const categoryLower = analysis.category.toLowerCase().trim();
    // Check if category is an invalid term
    if (invalidTerms.some(term => categoryLower.includes(term))) {
      analysis.category = 'shirt'; // Default fallback
    } else {
      const isValidCategory = validCategories.some(cat => cat.toLowerCase() === categoryLower);
      
      if (!isValidCategory) {
        // Try to infer from the category string
        if (categoryLower.includes('boot') || categoryLower.includes('sneaker') || 
            categoryLower.includes('sandal') || categoryLower.includes('heel') || 
            categoryLower.includes('flat') || categoryLower.includes('shoe')) {
          analysis.category = 'shoes';
        } else if (categoryLower.includes('dress')) {
          analysis.category = 'dress';
        } else if (categoryLower.includes('pant') || categoryLower.includes('jean') || 
                   categoryLower.includes('trouser')) {
          analysis.category = 'pants';
        } else if (categoryLower.includes('jacket') || categoryLower.includes('coat') || 
                   categoryLower.includes('sweater')) {
          analysis.category = 'jacket';
        } else {
          analysis.category = 'shirt';
        }
      }
    }
  }
  if (!analysis.color || analysis.color.trim() === '') {
    analysis.color = 'white';
  } else {
    const colorLower = analysis.color.toLowerCase().trim();
    // Check if color is an invalid term
    if (invalidTerms.some(term => colorLower.includes(term))) {
      analysis.color = 'white'; // Default fallback
    } else {
      // Try to infer color - check for brown/beige/green before white
      if (colorLower.includes('brown') || colorLower.includes('tan') || 
          colorLower.includes('camel') || colorLower.includes('taupe') ||
          colorLower.includes('suede') || colorLower.includes('leather')) {
        analysis.color = 'brown';
      } else if (colorLower.includes('beige') || colorLower.includes('nude') || 
                 colorLower.includes('sand') || colorLower.includes('cream')) {
        analysis.color = 'beige';
      } else if (colorLower.includes('green') || colorLower.includes('mint') || 
                 colorLower.includes('olive') || colorLower.includes('emerald') ||
                 colorLower.includes('sage') || colorLower.includes('forest')) {
        analysis.color = 'green';
      }
    }
  }
  if (!analysis.style || analysis.style.trim() === '') {
    analysis.style = 'casual';
  } else {
    const styleLower = analysis.style.toLowerCase().trim();
    // Check if style is an invalid term
    if (invalidTerms.some(term => styleLower.includes(term))) {
      analysis.style = 'casual'; // Default fallback
    } else {
      // Check if style is valid
      const isValidStyle = validStyles.some(s => s.toLowerCase() === styleLower);
      if (!isValidStyle) {
        analysis.style = 'casual'; // Default fallback
      }
    }
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
