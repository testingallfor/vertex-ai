![ga4](https://www.google-analytics.com/collect?v=2&tid=G-6VDTYWLKX6&cid=1&en=page_view&sid=1&dl=statmike%2Fvertex-ai-mlops%2FApplied+GenAI%2FVertex+AI+Search&dt=readme.md)

# /Applied GenAI/Vertex AI Search/readme.md

This series of notebooks highlights the use over [Vertex AI Search](https://cloud.google.com/generative-ai-app-builder/docs/try-enterprise-search) for workflows that includes using Google's [foundational large generative AI models](https://cloud.google.com/vertex-ai/docs/generative-ai/learn/models). These don't need to be trained or hosted - just called with via API. Read more about these exciting new features of Vertex AI Search (formerly named Generative AI App Builder Enterprise Search) [here](https://cloud.google.com/generative-ai-app-builder/docs/try-enterprise-search)


## About Vertex AI Search
Vertex AI Search is a part of the Vertex AI suite of tools offered by Google Cloud.

Vertex AI Search lets developers, even those with limited machine learning skills, quickly and easily tap into the power of Google’s foundation models and search expertise to create enterprise-grade generative AI applications. Vertex AI Search lets organizations quickly build generative AI powered search engines for customers and employees. The solution is provided within the Google Cloud Console UI and also via API for integration with enterprise workflows or large language models as shown in this repository.

## Using Vertex AI Search
Vertex AI Search is generally available in Google Cloud.

Upload data in the form of unstructued documents, web sites or relational databases and the users can retrieve the most relevant document chunks using natural language queries. The API is provided with specific configuration options which are designed to work well in conjunction with LLMs, such as choosing different document chunk types.

Vertex AI Search can provide search [snippets, extractive answers, and extractive segments](https://cloud.google.com/generative-ai-app-builder/docs/snippets#extractive-segments) with each search response to enhance your results.

## Combining Vertex AI Search with LLMs

As LLMs continue to explode in power and popularity, it has become increasingly clear that tools for information retrieval are an essential part of the stack to unlock many of Gen AI's most valuable use cases. These retrieval tools allow you to efficiently fetch information from your own data and insert the most relevant extracts directly into LLM prompts as context, for grounding the LLM. This allows you to ground Generative AI responses in data that you know to be relevant, validated and up to date.

Most approaches to retrieval typically require subsetting documents and other information into chunks, then creating embeddings from the chunks and the setting up of a vector search engine to match and retrieve related chunks. Custom solutions such as these can be time consuming and complex to create, maintain and host. In contrast, Vertex AI Search is a turnkey search engine which provides Google-quality results as a managed service.

## Getting Started

**Install**

The Vertex AI [Python Client](https://cloud.google.com/python/docs/reference/aiplatform/latest) will need to be updated to at least the 1.25.0 release.

Th Vertex AI Search [Python Client](https://cloud.google.com/generative-ai-app-builder/docs/libraries#client-libraries-install-python) will need to be installed.

## Notebooks For Document Q&A Examples:

Demonstrate the use of **Vertex AI Search with Extractive Segments**:
- [Vertex AI Search Document Q&A Using Extractive Segments - MLB Rules For Baseball.ipynb](./Vertex%20AI%20Search%20Document%20Q&A%20Using%20Extractive%20Segments%20-%20MLB%20Rules%20For%20Baseball.ipynb)
    - Ask questions related to the MLB Baseball rules and get text generated answers using the combination of both Vertex AI Search and Vertex GenAI LLMs.

## Vertex AI Search Setup:

The notebooks here use a Vertex Search environment setup with the simple steps covered in this [file](./vertex_search_setup.md)