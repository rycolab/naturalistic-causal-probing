class CacheBase():
    def __init__(self):
        self.is_valid = True
        self.prev_node = None
        self.cur_focus_idx = 0
        self.cur_adj_idx = 0
        self.cur_det_idx = 0
        self.target_focus_idx = 0
        self.dep_tree_size = 0
        self.cur_sent = ""
        self.cur_lemma = ""
        self.cur_gender = ""
        self.deprel = ""
        self.number = ""

    def reset_values(self):
        self.is_valid = True
        self.prev_node = None
        self.cur_focus_idx = 0
        self.target_focus_idx = 0
        self.cur_adj_idx = 0
        self.cur_det_idx = 0
        self.dep_tree_size = 0
        self.cur_sent = ""
        self.cur_lemma = ""
        self.cur_gender = ""
        self.deprel = ""
        self.number = ""
