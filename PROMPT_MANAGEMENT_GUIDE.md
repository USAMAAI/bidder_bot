# 📝 Admin Prompt Management Guide

## Overview

The UpworkScribe AI application now includes a powerful **Admin Prompt Management** system that allows administrators to customize the AI prompts used for generating cover letters and interview preparation scripts. This feature provides full control over how the AI responds to job applications while maintaining consistency across all users.

## Features

### 🔧 What You Can Do

- **Customize Cover Letter Prompts**: Define exactly how cover letters should be structured, styled, and written
- **Customize Interview Prep Prompts**: Control the format and content of interview preparation scripts  
- **Real-time Updates**: Changes apply immediately to all new applications
- **Version Control**: Track when prompts were created and last updated
- **Admin-Only Access**: Only users with admin privileges can modify prompts
- **Fallback Protection**: System falls back to default prompts if custom ones are unavailable

### 📋 Prompt Types

1. **Cover Letter (`cover_letter`)**: Controls how personalized cover letters are generated
2. **Interview Preparation (`interview_prep`)**: Controls how interview scripts and questions are created

## How to Access

1. **Login as Admin**: Must have administrator privileges
2. **Navigate to Admin Panel**: Click "👑 Admin Panel" in the sidebar
3. **Select Prompt Management**: Choose "📝 Prompt Management" from the admin sections

## Using the Prompt Management Interface

### 📖 Viewing Current Prompts

- All active prompts are displayed with expandable previews
- Shows prompt name, type, creation/update dates, and creator
- Preview shows first 300 characters of the prompt content

### ➕ Creating/Editing Prompts

1. **Choose Prompt Type**: Select either "cover_letter" or "interview_prep"
2. **Enter Prompt Name**: Give your prompt a descriptive name
3. **Write Prompt Content**: Use the large text area to create your prompt
4. **Use Placeholders**: Include `{profile}` where you want freelancer profile info
5. **Save**: Click "💾 Save Prompt" to apply changes

### ✏️ Editing Existing Prompts

1. **Click Edit Button**: Use the "✏️ Edit" button next to any prompt
2. **Modify Content**: Update the prompt name or content as needed
3. **Update**: Click "💾 Update Prompt" to save changes
4. **Cancel**: Use "❌ Cancel Edit" to discard changes

### 🗑️ Deleting Prompts

- Click the "🗑️ Delete" button next to any prompt
- Deletion is immediate and will revert to default system prompts
- **Warning**: This action cannot be undone

## Writing Effective Prompts

### 🎯 Best Practices

#### For Cover Letters:
- **Set Clear Tone**: Specify if formal, casual, or professional
- **Define Structure**: Outline introduction, body, and conclusion format
- **Set Word Limits**: Include maximum word count (e.g., "under 150 words")
- **Include Examples**: Provide sample format or style references
- **Specify Requirements**: Include name inclusion, signature format, etc.

#### For Interview Preparation:
- **Request Structure**: Ask for organized sections (intro, key points, questions)
- **Set Question Counts**: Specify how many questions to generate
- **Include Both Sides**: Request both client questions and questions to ask
- **Define Output Format**: Request markdown, bullet points, or specific formatting

### 📝 Prompt Template Variables

- **`{profile}`**: Replaced with the freelancer's complete profile information
- Use this placeholder wherever you want personalized content based on the user's skills, experience, and background

### 💡 Example Prompt Structures

#### Cover Letter Template:
```
You are a professional cover letter specialist creating targeted proposals.

Freelancer Profile:
{profile}

Instructions:
1. Write in a friendly, professional tone
2. Keep under 150 words
3. Address client needs directly
4. Highlight 2-3 relevant skills/experiences
5. Include genuine enthusiasm
6. End with freelancer's name

Format:
- Greeting
- Value proposition
- Relevant experience (bullet points)
- Call to action
- Professional closing
```

#### Interview Prep Template:
```
You are an interview preparation coach. Create a comprehensive interview script.

Freelancer Profile:
{profile}

Provide:
1. Professional introduction (30 seconds)
2. 5 key talking points about relevant experience
3. 10 potential client questions with suggested answers
4. 10 strategic questions to ask the client
5. Professional closing statements

Format all output in clean markdown with clear sections.
```

## 🚀 Getting Started

### Initialize Default Prompts

1. Go to **Admin Panel** → **📝 Prompt Management**
2. Click **"🔄 Initialize Default Prompts"**
3. This creates the base templates you can then customize

### Customize Your First Prompt

1. **Edit Cover Letter Prompt**:
   - Click "✏️ Edit" next to "Default Cover Letter Template"
   - Modify the content to match your preferred style
   - Update the prompt name to something descriptive
   - Save your changes

2. **Test the Changes**:
   - Process a job application
   - Review the generated cover letter
   - Iterate on the prompt as needed

## 🔄 How It Works

### System Integration

1. **Job Processing**: When generating applications, the system:
   - Checks for custom admin prompts in the database
   - Uses custom prompts if available
   - Falls back to hardcoded defaults if no custom prompts exist

2. **Profile Integration**: The `{profile}` placeholder gets replaced with:
   - User's skills and experience
   - Relevant project history
   - Education and certifications
   - Language capabilities
   - Other profile information

3. **Real-time Updates**: Changes to prompts apply immediately:
   - No app restart required
   - All new applications use updated prompts
   - Existing applications remain unchanged

## 🛡️ Security & Permissions

- **Admin Only**: Only users with `is_admin = 1` can access prompt management
- **Audit Trail**: All prompt changes are tracked with timestamps and creator info
- **Safe Fallbacks**: System continues working even if custom prompts are deleted
- **Input Validation**: Prompts are validated before saving

## 🔧 Troubleshooting

### Common Issues:

1. **"Access Denied" Error**:
   - Ensure your user account has admin privileges
   - Contact system administrator to promote your account

2. **Prompts Not Applying**:
   - Verify prompts are saved successfully
   - Check that prompt type matches exactly ("cover_letter" or "interview_prep")
   - Ensure `{profile}` placeholder is included where needed

3. **Database Errors**:
   - Run "🔄 Initialize/Upgrade Database" in System Tools
   - Contact technical support if errors persist

### Getting Help:

- **In-App Help**: Click "📖 Help" in the prompt form for quick reference
- **System Tools**: Use admin system tools for database maintenance
- **Logs**: Check application logs for detailed error information

## 📊 Best Results

### Tips for Optimal Performance:

1. **Test Incrementally**: Make small changes and test results
2. **Use Clear Instructions**: Be specific about formatting and requirements
3. **Include Examples**: Provide sample outputs when possible
4. **Monitor Results**: Review generated applications regularly
5. **Iterate Based on Feedback**: Refine prompts based on application success rates

### Measuring Success:

- Track application response rates
- Monitor interview callback frequency  
- Gather feedback from freelancers using the system
- A/B test different prompt variations

---

## 🎉 Conclusion

The Admin Prompt Management system gives you complete control over how your UpworkScribe AI generates applications. By customizing prompts to match your freelancers' needs and your business requirements, you can significantly improve application quality and success rates.

**Ready to get started?** Head to the Admin Panel and begin customizing your prompts today! 