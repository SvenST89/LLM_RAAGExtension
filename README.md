# LLM Retrieval-Augmented Answer Generation (RAAG) Model

## <font color="#9D9D9E">General Description</font>

This repository builds a customized GPT-Model with the [MistralAI 7B Instruct Model](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF) as provided on **Huggingface**.

The main notebook `customGPT_langchain.ipynb` starts by first setting up a corpus, does some **Semantic Search with cosine similarity** in order to find the best context for the LLM. Finally, a given query and the found context are given to the **Mistral AI LLM** in order to generate an answer.

As for corpus generation I have written several classes in `sst` which allow for retrieving data / information from a certain directory path. There are two classes `sst.pdf_extract.PDFExtract()` and in `sst.ppt_extract` you will find a class called `PPTExtract()` for retrieving textual data from powerpoint presentations.

The class `sst.pdf_extract.PDFExtract()` is based on [this Medium Article](https://towardsdatascience.com/extracting-text-from-pdf-files-with-python-a-comprehensive-guide-9fc4003d517). I extended its functionality and put everything into a class. Thanks for the great groundwork the colleague did in this article. As this code was again written in a 'hush-hush operation', please bear with me that the class might not be optimally structured.

So, if you use those "extraction"-classes in order to build up a corpus for your NLP work, then please consider that it might take a while. For instance, in this project I used as **example data** the **PDF of John Maynard Keynes and his "The General Theory of Employment Interest and Money"**. It has around 260 pages and it took easily 45 minutes to generate the corpus.

You need tesseract installed on your machine for PDF image extraction as it is used in the background - the `sst.pdf_extract.PDFExtract()` class makes a check whether `tesseract.exe` is available. If not, the code will break.

Once, we have the corpus prepared, we need to clean it and drop empty lines. This is done with some regex replacements in the main code file `customGPT_langchain.ipynb`.

In contrast to a **classification task in NLP** we do not need stopwords for cleaning the corpus. Also, compared to a **Speech-To-Text solution** we do not need to consider any lexicon / phoneme, lemmatization or stemming techniques for words. 

As we work with **Semantic Search** and **LLMs** which you directly work on the tokens as they are in order to generate sensible outputs, we can simply clean the corpus by deleting and replacing wrong / inappropriate tokens, respectively.

So having the corpus and given a `query`, we can continue with the class `sem_search.SemanticSearch()` in order to find the best `top_k_sent`-matches in the corpus. With the "best_match" variable we can then search in the dictionary returned by `sst.pdf_extract.PDFExtract()` for the respective page which contains this phrase and return the `page_content` to feed into the `llm` instance from `langchain.llms.CTransformers`, check [langchain docu here](https://python.langchain.com/docs/integrations/providers/ctransformers). The idea and guidance comes partly from my own experience at work as well as from [another great medium article](https://ai.plainenglish.io/️-langchain-streamlit-llama-bringing-conversational-ai-to-your-local-machine-a1736252b172).

As for the **Semantic Search** I have used a **sentence transformer model** (spec.: paraphrase-multilingual-MiniLM-L12-v2), found [here in the sbert Sentence Transformer Documentation](https://www.sbert.net/docs/pretrained_models.html). I did not do a reranking as I found that the results have not been better. I found that this model is working quite well. The sentence transformer class is easy to set on cuda/gpu-support with the `device` parameter.

## <font color="#9D9D9E">Requirements</font>

The required Python packages are collected in the `env.yml` file.

As for the system, check the following information:

<u>Hardware</u>

    - Windows 11 Home

    - CPU: 12th Gen Intel(R) Core(TM) i5-12500H, 12 cores, 16 logical processors

    - L1-Cache 1.1Mb, L2-Cache 9Mb, L3-Cache 18Mb

    - 16GB RAM

    - GPU 1: Intel(R) Iris(R) Xe Graphics, 7.8Gb

    - NVIDIA GPU: GeForce RTX 3050 Ti, 12Gb, dedicated storage 4Gb

<u>Software</u>

    - conda 23.10.0

    - Python 3.11.5

    - cuda, release 12.1, V12.1.105

    - Setup PyTorch (PyTorch version: 2.1.0) which is used in `sst.sem_search.SemanticSearch` : https://pytorch.org/get-started/locally/

    - tesseract v5.3.3.20231005. For installation on Windows I followed these instructions: https://linuxhint.com/install-tesseract-windows/
    

I used the `Accelerator()` library in order to make use of my GPU during inference of the LLM. See the code how to set it up. Also, I was able to extent the context length to 5000. Maybe more is possible for the Mistral AI model. Give it a try!

The answer was pretty fast. I received an answer within a minute.

The **dedicated Nvidia GPU storage was used at around $75$% of the capacity in order to run inference with the Mistral 7b model.**

I did not try it with the **Falcon 40b Instruct Open Assistant Model** (spec: falcon-40b-top1-560.ggccv1.q4_k.bin), which I have locally as well.