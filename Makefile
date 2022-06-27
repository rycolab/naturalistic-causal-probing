UD_DIR_BASE := data/ud

UDURL := https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-3226/ud-treebanks-v2.6.tgz

UD_DIR := $(UD_DIR_BASE)/ud-treebanks-v2.6
UD_FILE := $(UD_DIR_BASE)/ud-treebanks-v2.6.tgz

get_ud: $(UD_DIR)

# Get Universal Dependencies data
$(UD_DIR):
	echo "Get ud data"
	mkdir -p $(UD_DIR_BASE)
	wget -P $(UD_DIR_BASE) $(UDURL)
	tar -xvzf $(UD_FILE) -C $(UD_DIR_BASE)
