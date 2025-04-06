import logging
import math
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# States
MENU = 0

# Listening states
LISTENING = 1

# Reading states
READING_MODULE, READING_SCORE = range(2, 4)

# Writing states
WRITING_T1_TA, WRITING_T1_CC, WRITING_T1_LR, WRITING_T1_GRA = range(4, 8)
WRITING_T2_TR, WRITING_T2_CC, WRITING_T2_LR, WRITING_T2_GRA = range(8, 12)

# Speaking states
SPEAKING_FC, SPEAKING_LR, SPEAKING_GRA, SPEAKING_PR = range(12, 16)

# Overall states
OVERALL_MODULE = 16
OVERALL_L_TYPE, OVERALL_L_SCORE = range(17, 19)
OVERALL_R_TYPE, OVERALL_R_SCORE = range(19, 21)
OVERALL_W_SCORE, OVERALL_S_SCORE = range(21, 23)

# Listening conversion table
def listening_band(raw_score):
    if raw_score >= 39: return 9.0
    elif raw_score >= 37: return 8.5
    elif raw_score >= 35: return 8.0
    elif raw_score >= 32: return 7.5
    elif raw_score >= 30: return 7.0
    elif raw_score >= 26: return 6.5
    elif raw_score >= 23: return 6.0
    elif raw_score >= 18: return 5.5
    elif raw_score >= 16: return 5.0
    elif raw_score >= 13: return 4.5
    elif raw_score >= 10: return 4.0
    elif raw_score >= 8: return 3.5
    elif raw_score >= 6: return 3.0
    elif raw_score >= 4: return 2.5
    elif raw_score >= 2: return 2.0
    else: return 1.0

# Reading Academic conversion
def reading_academic_band(raw_score):
    if raw_score >= 39: return 9.0
    elif raw_score >= 37: return 8.5
    elif raw_score >= 35: return 8.0
    elif raw_score >= 33: return 7.5
    elif raw_score >= 30: return 7.0
    elif raw_score >= 27: return 6.5
    elif raw_score >= 23: return 6.0
    elif raw_score >= 19: return 5.5
    elif raw_score >= 15: return 5.0
    elif raw_score >= 13: return 4.5
    elif raw_score >= 10: return 4.0
    elif raw_score >= 8: return 3.5
    elif raw_score >= 6: return 3.0
    elif raw_score >= 4: return 2.5
    elif raw_score >= 2: return 2.0
    else: return 1.0

# Reading General Training conversion
def reading_general_band(raw_score):
    if raw_score >= 40: return 9.0
    elif raw_score >= 39: return 8.5
    elif raw_score >= 37: return 8.0
    elif raw_score >= 34: return 7.5
    elif raw_score >= 30: return 7.0
    elif raw_score >= 26: return 6.5
    elif raw_score >= 23: return 6.0
    elif raw_score >= 19: return 5.5
    elif raw_score >= 15: return 5.0
    elif raw_score >= 12: return 4.5
    elif raw_score >= 9: return 4.0
    elif raw_score >= 6: return 3.5
    elif raw_score >= 4: return 3.0
    elif raw_score >= 2: return 2.5
    else: return 1.0

# Round down to nearest 0.5 (IELTS criteria rounding)
def round_down_to_half(value):
    return math.floor(value * 2) / 2

# Round up to nearest 0.5 (IELTS overall rounding)
def round_up_to_half(value):
    return math.ceil(value * 2) / 2

def start(update: Update, context: CallbackContext) -> int:
    """Start the conversation and show main menu."""
    # Initialize data storage
    context.user_data.clear()
    
    show_menu(update)
    return MENU

def clear(update: Update, context: CallbackContext) -> int:
    """Clear conversation history and return to menu."""
    context.user_data.clear()
    
    update.message.reply_text(
        "✅ Conversation history has been cleared.\n\n"
        "Type /start to begin a new calculation.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return ConversationHandler.END

def show_menu(update: Update):
    """Show the main menu keyboard."""
    reply_keyboard = [
        ["🎧 Listening", "📖 Reading"],
        ["✍️ Writing", "🗣️ Speaking"],
        ["📊 Overall Score"]
    ]
    
    update.message.reply_text(
        "*Welcome to the IELTS Score Calculator Bot!* 📊\n\n"
        "Please select what you'd like to calculate:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )

def menu_choice(update: Update, context: CallbackContext) -> int:
    """Handle menu choices."""
    text = update.message.text
    
    if "🎧 Listening" in text:
        update.message.reply_text(
            "Please enter your raw *LISTENING* score (0 - 40):",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        return LISTENING
    
    elif "📖 Reading" in text:
        reply_keyboard = [["Academic", "General Training"]]
        update.message.reply_text(
            "Please select your IELTS module:",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return READING_MODULE
    
    elif "✍️ Writing" in text:
        update.message.reply_text(
            "Let's calculate your *WRITING* score.",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        
        update.message.reply_text(
            "*__Task 1__*\n\n"
            "Please enter your *Task Achievement (TA)* score (1.0 - 9.0):",
            parse_mode="Markdown"
        )
        return WRITING_T1_TA
    
    elif "🗣️ Speaking" in text:
        update.message.reply_text(
            "Let's calculate your *SPEAKING* score.\n\n"
            "Please enter your *Fluency & Coherence (FC)* score (1.0 - 9.0):",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        return SPEAKING_FC
    
    elif "📊 Overall Score" in text:
        reply_keyboard = [["Academic", "General Training"]]
        update.message.reply_text(
            "Let's calculate your overall IELTS score.\n\n"
            "First, please select your IELTS module:",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return OVERALL_MODULE
    
    else:
        show_menu(update)
        return MENU

# Validate band scores for Writing and Speaking
def validate_band_score(score_text):
    try:
        score = float(score_text)
        if score < 1.0 or score > 9.0:
            return None, "Please enter a valid band score between 1.0 and 9.0."
        return score, None
    except ValueError:
        return None, "Please enter a valid number (example: 6.5)."

# LISTENING SECTION
def listening_score(update: Update, context: CallbackContext) -> int:
    """Process listening raw score."""
    try:
        score = int(update.message.text)
        if 0 <= score <= 40:
            band_score = listening_band(score)
            
            result_message = f"🎧 *IELTS LISTENING Band Score*\n\n"
            result_message += f"Raw score: {score}/40\n"
            result_message += f"Band score: {band_score}"
            
            update.message.reply_text(result_message, parse_mode="Markdown")
            
            # End conversation with instruction to restart
            update.message.reply_text(
                "If you want to calculate again, use the /start command.",
                reply_markup=ReplyKeyboardRemove()
            )
            
            return ConversationHandler.END
        else:
            update.message.reply_text("Please enter a valid score between 0 and 40.")
            return LISTENING
    except ValueError:
        update.message.reply_text("Please enter a valid number between 0 and 40.")
        return LISTENING

# READING SECTION
def reading_module(update: Update, context: CallbackContext) -> int:
    """Handle reading module selection."""
    module = update.message.text
    
    if module in ["Academic", "General Training"]:
        context.user_data['module'] = module
        
        # First message with confirmation
        update.message.reply_text(
            f"✅ You selected: {module}",
            parse_mode="Markdown"
        )
        
        # Second message with next step
        update.message.reply_text(
            "Please enter your raw *READING* score (0 - 40):",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        
        return READING_SCORE
    else:
        reply_keyboard = [["Academic", "General Training"]]
        update.message.reply_text(
            "Please select a valid module using the keyboard buttons.",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return READING_MODULE

def reading_score(update: Update, context: CallbackContext) -> int:
    """Process reading raw score."""
    try:
        score = int(update.message.text)
        if 0 <= score <= 40:
            module = context.user_data.get('module', 'Academic')
            
            if module == "Academic":
                band_score = reading_academic_band(score)
            else:
                band_score = reading_general_band(score)
            
            result_message = f"📖 *IELTS READING Band Score*\n\n"
            result_message += f"Module: {module}\n"
            result_message += f"Raw score: {score}/40\n"
            result_message += f"Band score: {band_score}"
            
            update.message.reply_text(result_message, parse_mode="Markdown")
            
            # End conversation with instruction to restart
            update.message.reply_text(
                "If you want to calculate again, use the /start command.",
                reply_markup=ReplyKeyboardRemove()
            )
            
            return ConversationHandler.END
        else:
            update.message.reply_text("Please enter a valid score between 0 and 40.")
            return READING_SCORE
    except ValueError:
        update.message.reply_text("Please enter a valid number between 0 and 40.")
        return READING_SCORE

# WRITING SECTION
def writing_t1_ta(update: Update, context: CallbackContext) -> int:
    if not context.user_data.get('writing'):
        context.user_data['writing'] = {}
    
    score, error = validate_band_score(update.message.text)
    if error:
        update.message.reply_text(error)
        return WRITING_T1_TA
    
    context.user_data['writing']['t1_ta'] = score
    
    update.message.reply_text(
        f"✅ *__Task 1__*\n\n"
        f"*Task Achievement (TA)*: {score}",
        parse_mode="Markdown"
    )
    
    update.message.reply_text(
        "Please enter your *Coherence & Cohesion (CC)* score (1.0 - 9.0):",
        parse_mode="Markdown"
    )
    
    return WRITING_T1_CC

def writing_t1_cc(update: Update, context: CallbackContext) -> int:
    score, error = validate_band_score(update.message.text)
    if error:
        update.message.reply_text(error)
        return WRITING_T1_CC
    
    context.user_data['writing']['t1_cc'] = score
    
    update.message.reply_text(
        f"✅ *__Task 1__*\n\n"
        f"*Coherence & Cohesion (CC)*: {score}",
        parse_mode="Markdown"
    )
    
    update.message.reply_text(
        "Please enter your *Lexical Resource (LR)* score (1.0 - 9.0):",
        parse_mode="Markdown"
    )
    
    return WRITING_T1_LR

def writing_t1_lr(update: Update, context: CallbackContext) -> int:
    score, error = validate_band_score(update.message.text)
    if error:
        update.message.reply_text(error)
        return WRITING_T1_LR
    
    context.user_data['writing']['t1_lr'] = score
    
    update.message.reply_text(
        f"✅ *__Task 1__*\n\n"
        f"*Lexical Resource (LR)*: {score}",
        parse_mode="Markdown"
    )
    
    update.message.reply_text(
        "Please enter your *Grammatical Range & Accuracy (GRA)* score (1.0 - 9.0):",
        parse_mode="Markdown"
    )
    
    return WRITING_T1_GRA

def writing_t1_gra(update: Update, context: CallbackContext) -> int:
    score, error = validate_band_score(update.message.text)
    if error:
        update.message.reply_text(error)
        return WRITING_T1_GRA
    
    context.user_data['writing']['t1_gra'] = score
    
    update.message.reply_text(
        f"✅ *__Task 1__*\n\n"
        f"*Grammatical Range & Accuracy (GRA)*: {score}",
        parse_mode="Markdown"
    )
    
    update.message.reply_text(
        "*__Task 2__*\n\n"
        "Please enter your *Task Response (TR)* score (1.0 - 9.0):",
        parse_mode="Markdown"
    )
    
    return WRITING_T2_TR

def writing_t2_tr(update: Update, context: CallbackContext) -> int:
    score, error = validate_band_score(update.message.text)
    if error:
        update.message.reply_text(error)
        return WRITING_T2_TR
    
    context.user_data['writing']['t2_tr'] = score
    
    update.message.reply_text(
        f"✅ *__Task 2__*\n\n"
        f"*Task Response (TR)*: {score}",
        parse_mode="Markdown"
    )
    
    update.message.reply_text(
        "Please enter your *Coherence & Cohesion (CC)* score (1.0 - 9.0):",
        parse_mode="Markdown"
    )
    
    return WRITING_T2_CC

def writing_t2_cc(update: Update, context: CallbackContext) -> int:
    score, error = validate_band_score(update.message.text)
    if error:
        update.message.reply_text(error)
        return WRITING_T2_CC
    
    context.user_data['writing']['t2_cc'] = score
    
    update.message.reply_text(
        f"✅ *__Task 2__*\n\n"
        f"*Coherence & Cohesion (CC)*: {score}",
        parse_mode="Markdown"
    )
    
    update.message.reply_text(
        "Please enter your *Lexical Resource (LR)* score (1.0 - 9.0):",
        parse_mode="Markdown"
    )
    
    return WRITING_T2_LR

def writing_t2_lr(update: Update, context: CallbackContext) -> int:
    score, error = validate_band_score(update.message.text)
    if error:
        update.message.reply_text(error)
        return WRITING_T2_LR
    
    context.user_data['writing']['t2_lr'] = score
    
    update.message.reply_text(
        f"✅ *__Task 2__*\n\n"
        f"*Lexical Resource (LR)*: {score}",
        parse_mode="Markdown"
    )
    
    update.message.reply_text(
        "Please enter your *Grammatical Range & Accuracy (GRA)* score (1.0 - 9.0):",
        parse_mode="Markdown"
    )
    
    return WRITING_T2_GRA

def writing_t2_gra(update: Update, context: CallbackContext) -> int:
    score, error = validate_band_score(update.message.text)
    if error:
        update.message.reply_text(error)
        return WRITING_T2_GRA
    
    context.user_data['writing']['t2_gra'] = score
    
    # Calculate Writing score
    writing_data = context.user_data['writing']
    
    # Calculate Task 1 score (rounded DOWN)
    t1_scores = [
        writing_data['t1_ta'],
        writing_data['t1_cc'],
        writing_data['t1_lr'],
        writing_data['t1_gra']
    ]
    t1_average = sum(t1_scores) / len(t1_scores)
    t1_score = round_down_to_half(t1_average)
    
    # Calculate Task 2 score (rounded DOWN)
    t2_scores = [
        writing_data['t2_tr'],
        writing_data['t2_cc'],
        writing_data['t2_lr'],
        writing_data['t2_gra']
    ]
    t2_average = sum(t2_scores) / len(t2_scores)
    t2_score = round_down_to_half(t2_average)
    
    # Calculate overall Writing score (Task 1 is 1/3, Task 2 is 2/3, rounded UP)
    overall_writing = (t1_score * 1/3) + (t2_score * 2/3)
    overall_writing_score = round_up_to_half(overall_writing)
    
    result_message = f"✍️ *IELTS WRITING Band Score*\n\n"
    result_message += f"*Task 1 Score:* {t1_score}\n"
    result_message += f"*Task 2 Score:* {t2_score}\n\n"
    result_message += f"*Overall Writing Score:* {overall_writing_score}"
    
    update.message.reply_text(
        result_message,
        parse_mode="Markdown",
    )
    
    # End conversation with instruction to restart
    update.message.reply_text(
        "If you want to calculate again, use the /start command.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return ConversationHandler.END

# SPEAKING SECTION
def speaking_fc(update: Update, context: CallbackContext) -> int:
    if not context.user_data.get('speaking'):
        context.user_data['speaking'] = {}
    
    score, error = validate_band_score(update.message.text)
    if error:
        update.message.reply_text(error)
        return SPEAKING_FC
    
    context.user_data['speaking']['fc'] = score
    
    update.message.reply_text(
        f"✅ *Fluency & Coherence (FC)*: {score}",
        parse_mode="Markdown"
    )
    
    update.message.reply_text(
        "Please enter your *Lexical Resource (LR)* score (1.0 - 9.0):",
        parse_mode="Markdown"
    )
    
    return SPEAKING_LR

def speaking_lr(update: Update, context: CallbackContext) -> int:
    score, error = validate_band_score(update.message.text)
    if error:
        update.message.reply_text(error)
        return SPEAKING_LR
    
    context.user_data['speaking']['lr'] = score
    
    update.message.reply_text(
        f"✅ *Lexical Resource (LR)*: {score}",
        parse_mode="Markdown"
    )
    
    update.message.reply_text(
        "Please enter your *Grammatical Range & Accuracy (GRA)* score (1.0 - 9.0):",
        parse_mode="Markdown"
    )
    
    return SPEAKING_GRA

def speaking_gra(update: Update, context: CallbackContext) -> int:
    score, error = validate_band_score(update.message.text)
    if error:
        update.message.reply_text(error)
        return SPEAKING_GRA
    
    context.user_data['speaking']['gra'] = score
    
    update.message.reply_text(
        f"✅ *Grammatical Range & Accuracy (GRA)*: {score}",
        parse_mode="Markdown"
    )
    
    update.message.reply_text(
        "Please enter your *Pronunciation (Pr)* score (1.0 - 9.0):",
        parse_mode="Markdown"
    )
    
    return SPEAKING_PR

def speaking_pr(update: Update, context: CallbackContext) -> int:
    score, error = validate_band_score(update.message.text)
    if error:
        update.message.reply_text(error)
        return SPEAKING_PR
    
    context.user_data['speaking']['pr'] = score
    
    # Calculate Speaking score
    speaking_data = context.user_data['speaking']
    
    # Get all scores
    scores = [
        speaking_data['fc'],
        speaking_data['lr'],
        speaking_data['gra'],
        speaking_data['pr']
    ]
    
    # Calculate average and round DOWN as specified
    average = sum(scores) / len(scores)
    speaking_score = round_down_to_half(average)
    
    result_message = f"🗣️ *IELTS SPEAKING Band Score*\n\n"
    result_message += f"*Fluency & Coherence*: {speaking_data['fc']}\n"
    result_message += f"*Lexical Resource*: {speaking_data['lr']}\n"
    result_message += f"*Grammatical Range & Accuracy*: {speaking_data['gra']}\n"
    result_message += f"*Pronunciation*: {speaking_data['pr']}\n\n"
    result_message += f"*Overall Speaking Score:* {speaking_score}"
    
    update.message.reply_text(
        result_message,
        parse_mode="Markdown",
    )
    
    # End conversation with instruction to restart
    update.message.reply_text(
        "If you want to calculate again, use the /start command.", 
        reply_markup=ReplyKeyboardRemove()
    )
    
    return ConversationHandler.END

# OVERALL SCORE SECTION
def overall_module(update: Update, context: CallbackContext) -> int:
    if not context.user_data.get('overall'):
        context.user_data['overall'] = {}
    
    module = update.message.text
    
    if module in ["Academic", "General Training"]:
        context.user_data['overall']['module'] = module
        
        # First message with confirmation
        update.message.reply_text(
            f"✅ You selected: {module} module",
            parse_mode="Markdown"
        )
        
        # Second message asking for listening type
        reply_keyboard = [["Raw Score (0 - 40)", "Band Score (1.0 - 9.0)"]]
        update.message.reply_text(
            "For *LISTENING*, do you want to enter a raw score or band score?",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        
        return OVERALL_L_TYPE
    else:
        reply_keyboard = [["Academic", "General Training"]]
        update.message.reply_text(
            "Please select a valid module using the keyboard buttons.",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return OVERALL_MODULE

def overall_listening_type(update: Update, context: CallbackContext) -> int:
    choice = update.message.text
    
    if "Raw Score" in choice:
        context.user_data['overall']['listening_type'] = 'raw'
        
        # Confirmation message
        update.message.reply_text(
            "✅ You selected: Raw Score input",
            parse_mode="Markdown"
        )
        
        # Request input message
        update.message.reply_text(
            "Please enter your raw *LISTENING* score (0 - 40):",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
    elif "Band Score" in choice:
        context.user_data['overall']['listening_type'] = 'band'
        
        # Confirmation message
        update.message.reply_text(
            "✅ You selected: Band Score input",
            parse_mode="Markdown"
        )
        
        # Request input message
        update.message.reply_text(
            "Please enter your *LISTENING* band score (1.0 - 9.0):",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        reply_keyboard = [["Raw Score (0 - 40)", "Band Score (1.0 - 9.0)"]]
        update.message.reply_text(
            "Please select a valid option.",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return OVERALL_L_TYPE
    
    return OVERALL_L_SCORE

def overall_listening_score(update: Update, context: CallbackContext) -> int:
    listening_type = context.user_data['overall'].get('listening_type', 'band')
    
    try:
        score = float(update.message.text)
        
        # Validate score based on type
        if listening_type == 'raw':
            if 0 <= score <= 40:
                # Convert raw score to band score
                band_score = listening_band(int(score))
                context.user_data['overall']['listening'] = band_score
                
                # First message with confirmation
                update.message.reply_text(
                    f"✅ *LISTENING* raw score: {int(score)}/40 → Band score: {band_score}",
                    parse_mode="Markdown"
                )
                
                # Second message asking for reading type
                reply_keyboard = [["Raw Score (0 - 40)", "Band Score (1.0 - 9.0)"]]
                update.message.reply_text(
                    "For *READING*, do you want to enter a raw score or band score?",
                    parse_mode="Markdown",
                    reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
                )
                
                return OVERALL_R_TYPE
            else:
                update.message.reply_text("Please enter a valid raw score between 0 and 40.")
                return OVERALL_L_SCORE
                
        elif listening_type == 'band':
            if 1.0 <= score <= 9.0:
                # Store band score directly
                context.user_data['overall']['listening'] = score
                
                # First message with confirmation
                update.message.reply_text(
                    f"✅ *LISTENING* band score: {score}",
                    parse_mode="Markdown"
                )
                
                # Second message asking for reading type
                reply_keyboard = [["Raw Score (0 - 40)", "Band Score (1.0 - 9.0)"]]
                update.message.reply_text(
                    "For *READING*, do you want to enter a raw score or band score?",
                    parse_mode="Markdown",
                    reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
                )
                
                return OVERALL_R_TYPE
            else:
                update.message.reply_text("Please enter a valid band score between 1.0 and 9.0.")
                return OVERALL_L_SCORE
    except ValueError:
        update.message.reply_text("Please enter a valid number.")
        return OVERALL_L_SCORE

def overall_reading_type(update: Update, context: CallbackContext) -> int:
    choice = update.message.text
    
    if "Raw Score" in choice:
        context.user_data['overall']['reading_type'] = 'raw'
        
        # Confirmation message
        update.message.reply_text(
            "✅ You selected: Raw Score input",
            parse_mode="Markdown"
        )
        
        # Request input message
        update.message.reply_text(
            "Please enter your raw *READING* score (0 - 40):",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
    elif "Band Score" in choice:
        context.user_data['overall']['reading_type'] = 'band'
        
        # Confirmation message
        update.message.reply_text(
            "✅ You selected: Band Score input",
            parse_mode="Markdown"
        )
        
        # Request input message
        update.message.reply_text(
            "Please enter your *READING* band score (1.0 - 9.0):",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        reply_keyboard = [["Raw Score (0 - 40)", "Band Score (1.0 - 9.0)"]]
        update.message.reply_text(
            "Please select a valid option.",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return OVERALL_R_TYPE
    
    return OVERALL_R_SCORE

def overall_reading_score(update: Update, context: CallbackContext) -> int:
    reading_type = context.user_data['overall'].get('reading_type', 'band')
    module = context.user_data['overall'].get('module', 'Academic')
    
    try:
        score = float(update.message.text)
        
        # Validate score based on type
        if reading_type == 'raw':
            if 0 <= score <= 40:
                # Convert raw score to band score based on module
                if module == 'Academic':
                    band_score = reading_academic_band(int(score))
                else:
                    band_score = reading_general_band(int(score))
                
                context.user_data['overall']['reading'] = band_score
                
                # First message with confirmation
                update.message.reply_text(
                    f"✅ *READING* raw score: {int(score)}/40 → Band score: {band_score}",
                    parse_mode="Markdown"
                )
                
                # Second message asking for writing score
                update.message.reply_text(
                    "Please enter your *WRITING* band score (1.0 - 9.0):",
                    parse_mode="Markdown"
                )
                
                return OVERALL_W_SCORE
            else:
                update.message.reply_text("Please enter a valid raw score between 0 and 40.")
                return OVERALL_R_SCORE
                
        elif reading_type == 'band':
            if 1.0 <= score <= 9.0:
                # Store band score directly
                context.user_data['overall']['reading'] = score
                
                # First message with confirmation
                update.message.reply_text(
                    f"✅ *READING* band score: {score}",
                    parse_mode="Markdown"
                )
                
                # Second message asking for writing score
                update.message.reply_text(
                    "Please enter your *WRITING* band score (1.0 - 9.0):",
                    parse_mode="Markdown"
                )
                
                return OVERALL_W_SCORE
            else:
                update.message.reply_text("Please enter a valid band score between 1.0 and 9.0.")
                return OVERALL_R_SCORE
    except ValueError:
        update.message.reply_text("Please enter a valid number.")
        return OVERALL_R_SCORE

def overall_writing_score(update: Update, context: CallbackContext) -> int:
    score, error = validate_band_score(update.message.text)
    if error:
        update.message.reply_text(error)
        return OVERALL_W_SCORE
    
    context.user_data['overall']['writing'] = score
    
    # First message with confirmation
    update.message.reply_text(
        f"✅ *WRITING* band score: {score}",
        parse_mode="Markdown"
    )
    
    # Second message asking for speaking score
    update.message.reply_text(
        "Please enter your *SPEAKING* band score (1.0 - 9.0):",
        parse_mode="Markdown"
    )
    
    return OVERALL_S_SCORE

def overall_speaking_score(update: Update, context: CallbackContext) -> int:
    score, error = validate_band_score(update.message.text)
    if error:
        update.message.reply_text(error)
        return OVERALL_S_SCORE
    
    context.user_data['overall']['speaking'] = score
    
    # Calculate Overall IELTS score
    overall_data = context.user_data['overall']
    
    # Get all scores
    scores = [
        overall_data['listening'],
        overall_data['reading'],
        overall_data['writing'],
        overall_data['speaking']
    ]
    
    # Calculate average and round UP to nearest 0.5
    average = sum(scores) / len(scores)
    overall_score = round_up_to_half(average)
    
    result_message = f"📊 *IELTS Overall Band Score*\n\n"
    result_message += f"Module: {overall_data['module']}\n\n"
    result_message += f"🎧 *LISTENING*: {overall_data['listening']}\n"
    result_message += f"📖 *READING*: {overall_data['reading']}\n"
    result_message += f"✍️ *WRITING*: {overall_data['writing']}\n"
    result_message += f"🗣️ *SPEAKING*: {overall_data['speaking']}\n\n"
    result_message += f"*Overall Band Score:* {overall_score}"
    
    update.message.reply_text(
        result_message,
        parse_mode="Markdown",
    )
    
    # End conversation with instruction to restart
    update.message.reply_text(
        "If you want to calculate again, use the /start command.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Operation cancelled. Send /start to begin again.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text(
        "*IELTS Score Calculator Bot Commands*\n\n"
        "/start - Start a new IELTS score calculation\n"
        "/clear - Clear conversation history\n"
        "/help - Show this help message\n"
        "/cancel - Cancel current calculation",
        parse_mode="Markdown"
    )

def main() -> None:
    # Create the Updater
    token = os.getenv('TOKEN')
    if not token:
        raise ValueError("No TOKEN found in environment variables")
    updater = Updater(token)
    
    # Get the dispatcher
    dispatcher = updater.dispatcher
    
    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [MessageHandler(Filters.text & ~Filters.command, menu_choice)],
            
            # Listening states
            LISTENING: [MessageHandler(Filters.text & ~Filters.command, listening_score)],
            
            # Reading states
            READING_MODULE: [MessageHandler(Filters.text & ~Filters.command, reading_module)],
            READING_SCORE: [MessageHandler(Filters.text & ~Filters.command, reading_score)],
            
            # Writing states
            WRITING_T1_TA: [MessageHandler(Filters.text & ~Filters.command, writing_t1_ta)],
            WRITING_T1_CC: [MessageHandler(Filters.text & ~Filters.command, writing_t1_cc)],
            WRITING_T1_LR: [MessageHandler(Filters.text & ~Filters.command, writing_t1_lr)],
            WRITING_T1_GRA: [MessageHandler(Filters.text & ~Filters.command, writing_t1_gra)],
            WRITING_T2_TR: [MessageHandler(Filters.text & ~Filters.command, writing_t2_tr)],
            WRITING_T2_CC: [MessageHandler(Filters.text & ~Filters.command, writing_t2_cc)],
            WRITING_T2_LR: [MessageHandler(Filters.text & ~Filters.command, writing_t2_lr)],
            WRITING_T2_GRA: [MessageHandler(Filters.text & ~Filters.command, writing_t2_gra)],
            
            # Speaking states
            SPEAKING_FC: [MessageHandler(Filters.text & ~Filters.command, speaking_fc)],
            SPEAKING_LR: [MessageHandler(Filters.text & ~Filters.command, speaking_lr)],
            SPEAKING_GRA: [MessageHandler(Filters.text & ~Filters.command, speaking_gra)],
            SPEAKING_PR: [MessageHandler(Filters.text & ~Filters.command, speaking_pr)],
            
            # Overall states
            OVERALL_MODULE: [MessageHandler(Filters.text & ~Filters.command, overall_module)],
            OVERALL_L_TYPE: [MessageHandler(Filters.text & ~Filters.command, overall_listening_type)],
            OVERALL_L_SCORE: [MessageHandler(Filters.text & ~Filters.command, overall_listening_score)],
            OVERALL_R_TYPE: [MessageHandler(Filters.text & ~Filters.command, overall_reading_type)],
            OVERALL_R_SCORE: [MessageHandler(Filters.text & ~Filters.command, overall_reading_score)],
            OVERALL_W_SCORE: [MessageHandler(Filters.text & ~Filters.command, overall_writing_score)],
            OVERALL_S_SCORE: [MessageHandler(Filters.text & ~Filters.command, overall_speaking_score)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),  # Add /start as fallback so it works anywhere
            CommandHandler("clear", clear),  # Add /clear as fallback so it works anywhere
        ],
    )
    
    dispatcher.add_handler(conv_handler)
    
    # Add standalone help command handler
    dispatcher.add_handler(CommandHandler("help", help_command))
    
    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()