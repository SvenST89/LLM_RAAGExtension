from sentence_transformers import SentenceTransformer, CrossEncoder, util
import torch
import pandas as pd
import logging
import sys

#================================================#
# SET LOGGING
#================================================#
logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(lineno)s - %(levelname)s - %(message)s')
logger.setLevel(logging.DEBUG)

# set logging handler in file
fileHandler = logging.FileHandler(filename="log/search.log", mode="w")
fileHandler.setFormatter(formatter)
fileHandler.setLevel(logging.DEBUG)
logger.addHandler(fileHandler)

# set logging handler in Console
# consoleHandler = logging.StreamHandler(sys.stdout)
# consoleHandler.setFormatter(formatter)
# consoleHandler.setLevel(logging.ERROR)
# logger.addHandler(consoleHandler)

class SemanticSearch:
    #################################################
    # COMPUTING SETUP
    #################################################
    # https://thegeeksdiary.com/2023/03/23/how-to-set-up-pytorch-with-gpu-support-on-windows-11-a-comprehensive-guide/
    # Check if PyTorch uses the GPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logging.info(f"PyTorch is using: {device}")
    
    # print Torch version
    logging.info(f"PyTorch version: {torch.__version__}")
    
    #================================================#
    # CLASS ATTRIBUTES. The same for each Class Object
    #================================================#
    model_path = r"C:\Users\svens\02_DataScience\00_ML\NLP\openModels\paraphrase-multilingual-MiniLM-L12-v2"
    model_path_rerank = ""
    
    #================================================#
    # INSTANCE ATTRIBUTES. The same for each Class Object
    #================================================#
    def __init__(self, query, top_k_sent, corpus: list):
        # check if corpus is list of sentences
        if not isinstance(corpus, list):
            raise TypeError("Corpus is not a list of passages/sentences!")
            
        self.query = query
        self.top_k_sent = top_k_sent
        self.corpus = corpus

        # Parameters Log
        logging.info("##################################################\n")
        logging.info("GIVEN PARAMETERS\n----------------------------------------------------------------------------------------------------------------------")
        logging.info(f"QUERY: {self.query}")
        logging.info(f"NUMBER OF TOP RESULTS SHOWN: {self.top_k_sent}")
        logging.info(f"Corpus is up to you...")
        logging.info("##################################################\n")
            
    #================================================#
    # METHODS
    #================================================#
    
    #------------------------------------------------------------------------------#
    # PROTECTED METHODS
    #------------------------------------------------------------------------------#
    # These are used inside this class within other methods, 
    # but is not used inside the main code on a class instance level.
    # For building the embedder and the cross encoder we need to
    # call the class "SemanticSearch" in order to address the class attributes.
    
    @staticmethod
    def build_embedder():
        return SentenceTransformer(model_name_or_path=SemanticSearch.model_path, device = SemanticSearch.device)
    
    #@staticmethod
    #def build_CrossEncoder():
        #return CrossEncoder(SemanticSearch.model_path_rerank, device = SemanticSearch.device)
    
    #------------------------------------------------------------------------------#
    # INSTANCE METHODS
    #------------------------------------------------------------------------------#
    def do_semantic_search(self):
        #logging.info(f"\n=============================================================\nINPUT/QUERY: {self.query}\n=============================================================\n")
        
        #================================#
        # SEMANTIC SEARCH
        #----------------------------------------------------#
        embedder = self.build_embedder()
        query_embedding = embedder.encode(self.query, convert_to_tensor=True, device = SemanticSearch.device)
        corpus_embeddings = embedder.encode(self.corpus, convert_to_tensor=True, device=SemanticSearch.device)
        logging.info("Embeddings calculated...\n")
        # Über Cosine-Similarity abgleichen, wie gut query semantisch zum Corpus passt
        cosine_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]
        top_results = torch.topk(cosine_scores, k=self.top_k_sent) # liefert einen tensor mit "values" = "score" und "indices" sind die corpus ids.
        # Die Ähnlichkeitsmetrik der query-corpus-vektoren befinden sich bei index '0' im tensor
        # copy gpu-tensor first to CPU, then transform into numpy array.
        scores = top_results[0].cpu().numpy()
        # ID in corpus, index 1 in tensor
        IDs = top_results[1].cpu().numpy()
        hits = []
        # mache list of dictionary, z. B. wie folgt: [{'corpus_id': 1, 'score':0.57}, {...}]
        for score, idx in zip(scores, IDs):
            top_dict = {}
            top_dict['corpus_id'] = idx
            top_dict['score'] = score
            hits.append(top_dict)
        
        #================================#
        # RERANKING OF RESULTS
        #----------------------------------------------------#
        #cross_inp = [[self.query, self.corpus[hit['corpus_id']]] for hit in hits]
        #cross_encoder = self.build_CrossEncoder()
        #cross_scores = cross_encoder.predict(cross_inp)
        
        # Sort results by cross-encoder scores
        #for idx in range(len(cross_scores)):
            #hits[idx]['cross-score'] = cross_scores[idx]
            
        
         #================================#
        # OUTPUS
        #----------------------------------------------------#
        # Output of top hits from Semantic Encoder
        #logging.info("Top Hits from the SEMANTIC SEARCH MODEL.")
        #logging.info("---------------------------------------------------------------------------\n")
        hits_sem = sorted(hits, key=lambda x: x['score'], reverse=True)
        result_list_sem = []
        for hit in hits_sem[0: int(self.top_k_sent)]:
            result_dict_sem = {}
            result_dict_sem['corpus_passage'] = self.corpus[hit['corpus_id']]
            result_dict_sem['score'] = hit['score']
            result_list_sem.append(result_dict_sem)
            #logging.info(self.corpus[hit['corpus_id']], "(Score: {:.4f})".format(hit['score']))
            
        
        # SEMANTIC RESULTS
        result_df_sem = pd.DataFrame(result_list_sem)
        result_df_sem_unique = result_df_sem.drop_duplicates() # check all columns and drop duplicate rows
        result_df_sem_unique.to_csv("data/result_df_sem_unique.csv", index = False, header = True)
        
        return result_df_sem_unique