class BeekeeperPRBestPracticesFormatter:
    def format_guidelines(self, relevant_guidelines):
        """
        Extract guidelines from markdown content with the format:
        ## MUST/SHOULD/MAY guideline title <a href="#ID" id="ID">[ID]</a>

        Returns formatted guidelines as a list of strings.
        """
        formatted_guidelines = []
        import re

        for guideline_path, content in relevant_guidelines.items():
            markdown_content = content.get("markdown", "")
            file_types = content.get("file_types", [])

            # Determine category based on file_types
            category = "General"
            if file_types:
                # Use the first file type as the category
                category = file_types[0].capitalize()

            # Match headers with their IDs
            pattern = r'#+\s+(.*?)\s+<a href="#(\d+)" id="\d+">\[(\d+)\]</a>'
            matches = re.findall(pattern, markdown_content)

            for match in matches:
                title, _, guideline_id = match

                # Check if the title contains MUST/SHOULD/MAY
                importance = "MUST"  # Default
                for keyword in ["MUST", "SHOULD", "MAY"]:
                    if keyword in title:
                        importance = keyword
                        break

                # Format the guideline with category-id format
                guideline_text = f"- **[{category}-{guideline_id}]** {title.strip()}"
                formatted_guidelines.append(guideline_text)

        return "\n".join(formatted_guidelines) if formatted_guidelines else ""