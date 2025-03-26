"""Helper methods for research processing"""

from typing import Dict, Any, List, Optional, Tuple
from tavily import TavilyClient

from . import logger
from .config import get_config
from .bedrock_utils import get_bedrock_response, query_knowledge_base, ModelSize
from .ai_utils import get_prompt, Prompts, extract_structured_data
from .web_utils import scrape_website
from .types import PortfolioCompany


def identify_company_in_query(
    query: str, companies: List[PortfolioCompany]
) -> Optional[Dict[str, Any]]:
    """
    Identify which company is being mentioned in the user query using AI analysis.

    This function uses the Bedrock AI service to analyze the user's query and
    determine which portfolio company they are asking about. It handles both
    explicit company mentions and implicit references.

    Args:
        query: The user query text to analyze for company references
        companies: List of portfolio companies to search against

    Returns:
        Company data dictionary with company information or None if no company identified

    Raises:
        ValueError: If query or companies list is empty (handled internally)
    """
    if not query or not query.strip():
        logger.warning("Empty query provided to identify_company_in_query")
        return None

    if not companies:
        logger.warning("Empty companies list provided to identify_company_in_query")
        return None

    try:
        logger.info("Identifying company mentioned in query")

        # Create the prompt to identify company
        identify_company_prompt = get_prompt(
            Prompts.IDENTIFY_COMPANY,
            query=query,
            companies_list=companies,
        )

        # Get response from Bedrock
        identification_response = get_bedrock_response(
            identify_company_prompt, model_size=ModelSize.MEDIUM
        )

        if not identification_response:
            logger.warning(
                "No response received from Bedrock for company identification"
            )
            return None

        # Extract structured data from the response
        company_data = extract_structured_data(
            identification_response, expected_format="company identification"
        )

        if not company_data:
            logger.info("No company identified in user query")
            return None

        # Handle possible array response
        if isinstance(company_data, list) and company_data:
            company_data = company_data[0]

        logger.info(f"Identified company: {company_data.get('name', 'unknown')}")
        return company_data

    except ValueError as e:
        logger.error(f"Value error in company identification: {str(e)}")
        return None
    except KeyError as e:
        logger.error(f"Key error in company identification result: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error identifying company: {str(e)}")
        logger.exception("Full exception details:")
        return None


def gather_company_info(
    company_data: Dict[str, Any], deep_research: bool = False
) -> Tuple[Optional[str], Optional[str]]:
    """
    Gather information about a company by scraping relevant websites.

    This function scrapes both the EQT portfolio page for the company and the
    company's own website to gather comprehensive information. The scraping depth
    is adjusted based on the deep_research parameter.

    Args:
        company_data: Company information dictionary with URLs ('link' for EQT page and 'website' for company page)
        deep_research: Whether to perform deeper scraping with additional depth levels

    Returns:
        Tuple of (eqt_website_content, company_website_content) where each is a string of scraped content
        or None if scraping failed

    Raises:
        KeyError: If required URLs are missing from company data (handled internally)
        ValueError: If URLs are invalid (handled internally)
    """
    if not company_data:
        logger.error("Empty company data provided to gather_company_info")
        return None, None

    try:
        company_name = company_data.get("name", "the company")
        logger.info(f"Gathering information about {company_name}")

        # Set depth based on deep_research flag
        eqt_depth = 1
        # company_depth = 2 if deep_research else 1
        company_depth = 2

        # Scrape EQT website
        eqt_website = company_data.get("link")
        if not eqt_website:
            logger.error(
                "Missing required 'link' field in company data for EQT website"
            )
            return None, None

        if not eqt_website.startswith(("http://", "https://")):
            logger.error(f"Invalid EQT website URL format: {eqt_website}")
            return None, None

        eqt_web_content = scrape_website(eqt_website, eqt_depth)
        if not eqt_web_content:
            logger.warning(f"No content retrieved from EQT website: {eqt_website}")

        logger.info(
            f"EQT website content: {len(eqt_web_content)} chars from URL: {eqt_website}"
        )

        # Scrape company website
        company_website = company_data.get("website")
        if not company_website:
            logger.error("Missing required 'website' field in company data")
            return None, None

        if not company_website.startswith(("http://", "https://")):
            logger.error(f"Invalid company website URL format: {company_website}")
            return None, None

        company_web_content = scrape_website(company_website, company_depth)
        if not company_web_content:
            logger.warning(
                f"No content retrieved from company website: {company_website}"
            )

        logger.info(
            f"Company website content: {len(company_web_content)} chars from URL: {company_website}"
        )

        return eqt_web_content, company_web_content

    except ValueError as e:
        logger.error(f"Value error in gather_company_info: {str(e)}")
        logger.exception("Value error details:")
        return None, None
    except KeyError as e:
        logger.error(f"Missing required key in company data: {str(e)}")
        return None, None
    except Exception as e:
        logger.error(f"Unexpected error gathering company information: {str(e)}")
        logger.exception("Exception details:")
        return None, None


def reformulate_query(query: str) -> List[str]:
    """
    Reformulate the user query into two optimized knowledge base search queries.

    This function uses a medium-sized language model to analyze the original query
    and create two different search queries that approach the information need from
    complementary angles. These reformulated queries are optimized for knowledge base retrieval.

    Args:
        query: The original user query text

    Returns:
        List of reformulated query strings, typically containing two queries

    Raises:
        ValueError: If query is empty or invalid (handled internally)
    """
    if not query or not query.strip():
        logger.error("Empty query provided to reformulate_query")
        return []

    try:
        logger.info("Reformulating user query for knowledge base search")

        # Create reformulation prompt
        reformulation_prompt = get_prompt(Prompts.QUERY_REFORMULATION, query=query)

        if not reformulation_prompt:
            logger.error("Failed to generate query reformulation prompt")
            return []

        # Get reformulated queries from Bedrock using MEDIUM model
        response = get_bedrock_response(
            reformulation_prompt, model_size=ModelSize.MEDIUM
        )

        if not response:
            logger.warning("No response from Bedrock for query reformulation")
            return []

        # Extract structured data for reformulated queries
        result_data = extract_structured_data(
            response, expected_format="query reformulation"
        )

        # Validate response format
        if not result_data:
            logger.warning(
                "Failed to extract structured data from reformulation response"
            )
            return []

        reformulated_queries = result_data.get("reformulated_queries", [])
        if not reformulated_queries:
            logger.warning("No reformulated queries found in response")
            return []

        logger.info(
            f"Successfully reformulated query into {len(reformulated_queries)} queries"
        )
        return reformulated_queries

    except ValueError as e:
        logger.error(f"Value error in query reformulation: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error reformulating query: {str(e)}")
        logger.exception("Query reformulation exception:")
        return []


def query_internal_knowledge_base(query: str) -> Optional[str]:
    """
    Query the internal knowledge base for relevant information about the company.

    This function first reformulates the original query into two optimized search queries,
    then uses those to search the knowledge base for relevant documents. The results are
    combined and formatted into a readable markdown structure with source attribution.

    Args:
        query: The original user query text

    Returns:
        String containing formatted knowledge base results in markdown format,
        or None if no results available or the query failed

    Raises:
        ValueError: If knowledge base ID is not configured or parameters are invalid
        ConnectionError: If the connection to the knowledge base fails
    """

    if not query or not query.strip():
        logger.warning("Empty query provided to query_internal_knowledge_base")
        return None

    try:
        # Get knowledge base ID from config
        knowledge_base_id = get_config().get("KB_ID")
        if not knowledge_base_id:
            logger.warning(
                "Knowledge base ID not configured in environment, skipping knowledge retrieval"
            )
            return None

        # Step 1: Reformulate the original query for better retrieval
        logger.info("Reformulating query for knowledge base search")
        reformulated_queries = reformulate_query(query)

        queries = reformulated_queries if reformulated_queries else [query]

        # If query reformulation failed, fall back to original approach
        if not reformulated_queries:
            logger.warning("Query reformulation failed, using original query format")

        # Step 2: Perform multiple knowledge base queries with reformulated queries
        all_results = []

        for idx, reformulated_query in enumerate(queries, 1):

            search_query = reformulated_query

            logger.info(
                f"Searching internal knowledge base with query {idx}: {search_query}"
            )

            # Query the knowledge base
            kb_results = query_knowledge_base(
                query=search_query,
                knowledge_base_id=knowledge_base_id,
                max_results=5,  # Fewer results per query since we're doing multiple
            )

            if kb_results and kb_results.get("results"):
                # Add results from this query to our collection
                all_results.extend(kb_results.get("results", []))
            else:
                logger.warning(
                    f"No results for reformulated query {idx}: {search_query}"
                )

        # Check if we found any results across all queries
        if not all_results:
            logger.info(
                f"No relevant information found in knowledge base for the query"
            )
            return None

        # Format the knowledge base results
        formatted_results = []
        for i, result in enumerate(all_results, 1):
            try:
                content = result.get("content", {}).get("text", "")
                if not content:
                    continue

                metadata = result.get("metadata", {})
                source = metadata.get("source", "Internal document")
                formatted_results.append(f"### Result {i}: {source}\n{content}\n")
            except KeyError as ke:
                logger.warning(f"Unexpected knowledge base result format: {ke}")
                continue

        if formatted_results:
            kb_data = "\n".join(formatted_results)
            logger.info("Successfully retrieved insights from knowledge base")
            return kb_data

        logger.info("No usable content found in knowledge base results")
        return None

    except ValueError as e:
        logger.error(f"Value error in knowledge base query: {str(e)}")
        return None
    except ConnectionError as e:
        logger.error(f"Connection error accessing knowledge base: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error querying knowledge base: {str(e)}")
        logger.exception("Knowledge base query exception:")
        return None


def analyze_company_info(
    query: str,
    eqt_content: str,
    company_content: str,
    kb_data: Optional[str] = None,
    deep_research: bool = False,
) -> Optional[str]:
    """
    Analyze gathered company information and generate a comprehensive research summary.

    This function processes scraped website content from both EQT and the company website,
    along with optional knowledge base data, to generate a comprehensive analysis
    tailored to the user's original query. The analysis is generated using Bedrock AI
    with different model sizes based on the depth of research required.

    Args:
        query: The original user query to focus the analysis on
        eqt_content: Text content scraped from the EQT portfolio website
        company_content: Text content scraped from the company's own website
        kb_data: Optional knowledge base data from internal sources (defaults to None)
        deep_research: Whether to use more comprehensive analysis methods (defaults to False)

    Returns:
        Generated analysis text as a string, or None if the analysis failed

    Raises:
        ValueError: If input parameters are invalid (handled internally)
        RuntimeError: If AI model generation fails (handled internally)
    """
    if not query or not query.strip():
        logger.error("Empty query provided to analyze_company_info")
        return None

    if not eqt_content and not company_content:
        logger.error("No content provided to analyze_company_info")
        return None

    try:
        logger.info("Analyzing collected company information")

        # Build prompt arguments
        prompt_args = {
            "query": query,
            "eqt_web_content": eqt_content or "No EQT content available",
            "company_web_content": company_content
            or "No company website content available",
            "kb_data_section": "",  # Default to empty string
        }

        # Add knowledge base insights if available
        if kb_data:
            kb_section = (
                "## INTERNAL KNOWLEDGE BASE DATA\n"
                f"{kb_data}\n\n"
                "_This information was retrieved from the EQT internal knowledge base_\n"
            )
            prompt_args["kb_data_section"] = kb_section
            logger.info("Including knowledge base data in analysis prompt")
        else:
            logger.info("No knowledge base data available for inclusion in analysis")

        # Generate prompt with all available information
        web_content_prompt = get_prompt(Prompts.WEB_SUMMARY, **prompt_args)

        # Select model size based on deep research flag
        model_size = ModelSize.LARGE

        message = (
            "Generating comprehensive in-depth analysis"
            if deep_research
            else "Generating comprehensive response"
        )
        logger.info(message)

        # Generate and return the analysis
        response = get_bedrock_response(web_content_prompt, model_size=model_size)
        if not response:
            logger.error("Failed to get response from Bedrock AI model")
            return None

        logger.info(f"Successfully generated analysis of {len(response)} chars")
        return response

    except ValueError as e:
        logger.error(f"Value error in company analysis: {str(e)}")
        return None
    except RuntimeError as e:
        logger.error(f"Runtime error in AI analysis generation: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error analyzing company information: {str(e)}")
        logger.exception("Exception details:")
        return None


def generate_fallback_response(query: str) -> Optional[str]:
    """
    Generate a fallback response when no specific company is identified in the user query.

    This function uses a smaller, faster AI model to generate a helpful response when
    the system cannot identify which EQT portfolio company the user is asking about.
    The response explains the system's capabilities and limitations in a user-friendly way.

    Args:
        query: The original user query text that didn't match any company

    Returns:
        Generated fallback response text or None if generation failed

    Raises:
        ValueError: If query is empty or invalid (handled internally)
    """
    if not query or not query.strip():
        logger.error("Empty query provided to generate_fallback_response")
        return "I'm sorry, but I didn't receive a valid query to respond to."

    try:
        logger.info("Generating fallback response (no company identified)")

        no_company_found_prompt = get_prompt(Prompts.NO_COMPANY_PROMPT, query=query)

        if not no_company_found_prompt:
            logger.error("Failed to generate fallback prompt")
            return "I'm sorry, but I couldn't understand which company you're asking about."

        response = get_bedrock_response(
            no_company_found_prompt, model_size=ModelSize.SMALL
        )

        if not response:
            logger.error("Failed to get fallback response from Bedrock model")
            return "I'm sorry, but I can only provide information about specific EQT portfolio companies."

        logger.info(
            f"Successfully generated fallback response of {len(response)} chars"
        )
        return response

    except ValueError as e:
        logger.error(f"Value error in fallback response: {str(e)}")
        return "I'm sorry, but I encountered an error processing your query."
    except Exception as e:
        logger.error(f"Error generating fallback response: {str(e)}")
        logger.exception("Fallback response exception:")
        return "I'm sorry, but I can only provide information about specific EQT portfolio companies."


def identify_knowledge_gaps(query: str, current_analysis: str) -> List[Dict[str, Any]]:
    """
    Identify knowledge gaps in the current analysis that could benefit from further research.

    This function analyzes the current research content in the context of the original query
    to identify areas where additional information would improve the response. It uses
    an AI model to generate structured data about specific knowledge gaps and the
    search queries that could address them.

    Args:
        query: The original user query to use as context
        current_analysis: The current analysis text to analyze for gaps

    Returns:
        List of knowledge gap data objects, each containing:
        - gap_id: Unique identifier for the gap
        - description: Description of the knowledge gap
        - search_queries: List of search queries to address the gap

    Raises:
        ValueError: If input parameters are invalid (handled internally)
        KeyError: If the response structure is invalid (handled internally)
    """
    if not query or not query.strip():
        logger.error("Empty query provided to identify_knowledge_gaps")
        return []

    if not current_analysis or not current_analysis.strip():
        logger.error("Empty analysis provided to identify_knowledge_gaps")
        return []

    try:
        logger.info("Identifying knowledge gaps in research")

        # Create prompt to identify knowledge gaps
        knowledge_gaps_prompt = get_prompt(
            Prompts.KNOWLEDGE_GAPS,
            query=query,
            current_analysis=current_analysis,
        )

        if not knowledge_gaps_prompt:
            logger.error("Failed to generate knowledge gaps prompt")
            return []

        # Get response from Bedrock
        gap_response = get_bedrock_response(
            knowledge_gaps_prompt, model_size=ModelSize.MEDIUM
        )

        if not gap_response:
            logger.warning("No response from Bedrock for knowledge gaps identification")
            return []

        # Extract structured data for knowledge gaps
        gap_data = extract_structured_data(
            gap_response, expected_format="knowledge gaps"
        )

        # Validate response format
        if not gap_data:
            logger.warning(
                "Failed to extract structured data from knowledge gaps response"
            )
            return []

        if "knowledge_gaps" not in gap_data:
            logger.warning("Missing 'knowledge_gaps' key in response data")
            return []

        if not gap_data["knowledge_gaps"]:
            logger.info("No knowledge gaps identified in the current analysis")
            return []

        # Validate each knowledge gap has required fields
        valid_gaps = []
        for gap in gap_data["knowledge_gaps"]:
            if (
                "description" in gap
                and "search_queries" in gap
                and gap["search_queries"]
            ):
                valid_gaps.append(gap)
            else:
                logger.warning(f"Skipping invalid knowledge gap format: {gap}")

        logger.info(f"Identified {len(valid_gaps)} valid knowledge gaps")
        return valid_gaps

    except ValueError as e:
        logger.error(f"Value error identifying knowledge gaps: {str(e)}")
        return []
    except KeyError as e:
        logger.error(f"Key error in knowledge gaps response structure: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error identifying knowledge gaps: {str(e)}")
        logger.exception("Knowledge gap identification exception:")
        return []


def perform_research(knowledge_gaps: List[Dict[str, Any]]) -> List[str]:
    """
    Perform additional research based on identified knowledge gaps using external search.

    This function takes the knowledge gaps identified in the analysis and uses the Tavily
    search API to find additional information from the web. Each knowledge gap is researched
    using its associated search queries, and the results are formatted into markdown sections
    with the answer text and source attribution.

    Args:
        knowledge_gaps: List of knowledge gap data objects containing descriptions and search queries

    Returns:
        List of additional content sections in markdown format from research

    Raises:
        ValueError: If API key is missing or parameters are invalid (handled internally)
        ConnectionError: If connection to search API fails (handled internally)
    """
    if not knowledge_gaps:
        logger.info("No knowledge gaps provided for research")
        return []

    # Get Tavily API key from config
    tavily_api_key = get_config().get("TAVILY_API_KEY")
    if not tavily_api_key:
        logger.warning(
            "Tavily API key not configured in environment, skipping external research"
        )
        return []

    # Initialize Tavily client
    try:
        logger.info("Initializing Tavily research client")
        tavily_client = TavilyClient(api_key=tavily_api_key)
    except ValueError as e:
        logger.error(f"Invalid API key for Tavily client: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Failed to initialize Tavily client: {str(e)}")
        logger.exception("Tavily client initialization exception:")
        return []

    # Collect additional content
    additional_content = []
    logger.info(f"Researching {len(knowledge_gaps)} knowledge gaps")

    for gap_index, gap in enumerate(knowledge_gaps, 1):
        try:
            gap_description = gap.get("description", "")
            if not gap_description:
                gap_description = f"Additional Research Topic {gap_index}"

            search_queries = gap.get("search_queries", [])
            if not search_queries:
                logger.warning(
                    f"No search queries for knowledge gap: {gap_description}"
                )
                continue

            logger.info(f"Processing knowledge gap {gap_index}: {gap_description}")

            # Use the first query as primary, second as fallback
            primary_query = search_queries[0]

            try:
                # Search with Tavily
                logger.info(f"Searching Tavily for: {primary_query}")
                search_result = tavily_client.search(
                    query=primary_query,
                    search_depth="advanced",
                    include_domains=[],
                    exclude_domains=[],
                    include_answer=True,
                    max_results=3,
                )

                # Extract the answer and sources
                answer = search_result.get("answer", "")
                sources = search_result.get("results", [])

                if answer:
                    # Format the knowledge gap section
                    section = f"\n\n## {gap_description}\n\n{answer}\n\n"

                    # Add sources if available
                    if sources:
                        section += "**Sources:**\n"
                        for idx, source in enumerate(sources[:3], 1):
                            title = source.get("title", "Untitled")
                            url = source.get("url", "#")
                            section += f"{idx}. [{title}]({url})\n"

                    additional_content.append(section)
                    logger.info(f"Added research content for: {gap_description}")
                else:
                    logger.warning(f"No answer returned for query: {primary_query}")
                    # Try fallback immediately if no answer
                    raise ValueError("No answer in primary search result")

            except Exception as primary_error:
                logger.warning(f"Error in primary search: {str(primary_error)}")
                # Try fallback query if available
                if len(search_queries) > 1:
                    try:
                        fallback_query = search_queries[1]
                        logger.info(f"Trying fallback search for: {fallback_query}")
                        search_result = tavily_client.search(
                            query=fallback_query,
                            search_depth="basic",
                            include_answer=True,
                        )
                        answer = search_result.get("answer", "")
                        if answer:
                            section = f"\n\n## {gap_description}\n\n{answer}\n\n"
                            additional_content.append(section)
                            logger.info(
                                f"Added fallback research content for: {gap_description}"
                            )
                        else:
                            logger.warning(
                                f"No answer in fallback search for: {fallback_query}"
                            )
                    except Exception as fallback_error:
                        logger.error(f"Error in fallback search: {str(fallback_error)}")
                        logger.warning(f"Failed to research gap: {gap_description}")

        except Exception as gap_error:
            logger.error(
                f"Error processing knowledge gap {gap_index}: {str(gap_error)}"
            )
            continue

    logger.info(f"Completed research with {len(additional_content)} content sections")
    return additional_content


def incorporate_new_research(
    query: str, current_analysis: str, additional_content: List[str]
) -> str:
    """
    Incorporate additional research findings into the current analysis.

    This function takes newly researched information from external sources and
    uses an AI model to integrate it into the existing analysis, creating a more
    comprehensive and cohesive response that addresses the original query more fully.
    The integration maintains a consistent style and focuses on seamlessly incorporating
    the new information where relevant.

    Args:
        query: The original user query to maintain focus on the user's question
        current_analysis: Current analysis text to be enriched
        additional_content: List of additional content sections from external research

    Returns:
        Updated and enriched analysis text with new information integrated

    Raises:
        ValueError: If input parameters are invalid (handled internally)
    """
    if not additional_content:
        logger.info("No additional content to incorporate, returning original analysis")
        return current_analysis

    if not current_analysis or not current_analysis.strip():
        logger.error("Empty current analysis provided to incorporate_new_research")
        return ""

    if not query or not query.strip():
        logger.warning("Empty query provided to incorporate_new_research")
        # Continue with integration but note the warning

    try:
        logger.info(
            f"Enriching research with {len(additional_content)} additional information sections"
        )

        # Combine all additional content
        all_new_information = "\n\n# Additional Research\n\nThe following sections contain additional information gathered from external sources to enhance this analysis:"

        # Add all the additional content sections
        for section in additional_content:
            all_new_information += section

        # Create prompt to enrich research
        enrich_prompt = get_prompt(
            Prompts.ENRICH_RESEARCH,
            query=query,
            current_analysis=current_analysis,
            new_information=all_new_information,
        )

        if not enrich_prompt:
            logger.error("Failed to generate research enrichment prompt")
            return current_analysis

        # Get enriched analysis from Bedrock
        logger.info("Generating enriched analysis with new research information")
        enriched_analysis = get_bedrock_response(
            enrich_prompt, model_size=ModelSize.LARGE
        )

        if not enriched_analysis:
            logger.warning(
                "Failed to get response from Bedrock for research enrichment"
            )
            return current_analysis

        logger.info(
            f"Successfully enriched analysis (original: {len(current_analysis)} chars, new: {len(enriched_analysis)} chars)"
        )
        return enriched_analysis

    except ValueError as e:
        logger.error(f"Value error in research enrichment: {str(e)}")
        return current_analysis
    except Exception as e:
        logger.error(f"Unexpected error incorporating research: {str(e)}")
        logger.exception("Research incorporation exception:")
        # Return original analysis if we can't incorporate new research
        return current_analysis


def perform_deep_research_rounds(
    query: str, current_analysis: str, rounds: int = 1
) -> str:
    """
    Perform multiple rounds of deep research to progressively enrich the analysis.

    This function orchestrates an iterative research process where each round:
    1. Identifies knowledge gaps in the current analysis
    2. Performs external research to fill those gaps
    3. Incorporates the new research into the analysis

    Each round builds on the results of the previous round, creating increasingly
    comprehensive and detailed analysis. The process continues until either the
    specified number of rounds is completed or no further knowledge gaps are found.

    Args:
        query: The original user query to maintain focus on the user's question
        current_analysis: The starting analysis text to improve through research
        rounds: Number of research rounds to perform (default: 1)

    Returns:
        The enriched analysis text after all research rounds

    Raises:
        ValueError: If input parameters are invalid (handled internally)
    """
    if not query or not query.strip():
        logger.error("Empty query provided to perform_deep_research_rounds")
        return current_analysis

    if not current_analysis or not current_analysis.strip():
        logger.error("Empty current analysis provided to perform_deep_research_rounds")
        return ""

    if rounds < 1:
        logger.warning(f"Invalid rounds value: {rounds}, defaulting to 1")
        rounds = 1

    enriched_analysis = current_analysis
    logger.info(f"Starting deep research process with {rounds} round(s)")

    for round_num in range(1, rounds + 1):
        try:
            logger.info(f"Starting deep research round {round_num} of {rounds}")

            # Identify knowledge gaps
            knowledge_gaps = identify_knowledge_gaps(query, enriched_analysis)
            if not knowledge_gaps:
                logger.info(
                    f"No knowledge gaps found in round {round_num}, research complete"
                )
                break

            logger.info(
                f"Found {len(knowledge_gaps)} knowledge gaps in round {round_num}"
            )

            # Research the identified gaps
            additional_content = perform_research(knowledge_gaps)
            if not additional_content:
                logger.info(
                    f"No additional content found in round {round_num}, research complete"
                )
                break

            logger.info(
                f"Found {len(additional_content)} content sections in round {round_num}"
            )

            # Incorporate the research into the analysis
            previous_analysis = enriched_analysis
            enriched_analysis = incorporate_new_research(
                query, enriched_analysis, additional_content
            )

            # Check if the analysis actually changed
            if enriched_analysis == previous_analysis:
                logger.warning(
                    "Analysis did not change after incorporation, stopping research"
                )
                break

            logger.info(f"Successfully completed research round {round_num}")

        except ValueError as e:
            logger.error(f"Value error in research round {round_num}: {str(e)}")
            # Continue to next round if possible
            continue
        except Exception as e:
            logger.error(f"Unexpected error in research round {round_num}: {str(e)}")
            logger.exception(f"Research round {round_num} exception:")
            # Continue to next round if there's an error
            continue

    logger.info(f"Deep research process completed after {round_num} round(s)")
    return enriched_analysis
