import collections
import  json
import os


class Node:
    def __init__(self, number, parent=None,val=None, name=None, left=None, right=None):
        """number 必须要保证每个结点都是独一无二的，其他属性都可以 可存在可不存在"""
        self.number = number
        self.val = val
        self.name = name
        self.child=[]
        self.parent: 'Node'=parent
        if self.parent:
            self.level=self.parent.level+1
        else:
            self.level = -1
    def add(self,node):
        self.child.append(node)

# loaded_dataset=[]
# with open('/data/zlyuaj/muti-agent/fuzzing/output_mutated/original/code_round_0.jsonl', 'r') as f:
#     # 导入输出
#     loaded_dataset = [json.loads(line) for line in f]
counts=[]
end_node_lens=[]
all_path=os.listdir('.')
all_node=set()
for i in range(67):
    all_node.add(i)
all_path.sort()
for path in all_path:
    if path[0]=="_":
        continue
    # if '26' in path:
    #     continue
    for i in range(1):
        # if i==5:continue
        json_path='./'+path+'/_node_1000.jsonl'

        # json_path='/data/zlyuaj/muti-agent/fuzzing/output_fuzzing_one_per_time/pass@10/results-2024-12-18-20-00-34/_node_251.jsonl'
        # log_path='../../output_fuzz_pass@10_analyst_score_all_plan.txt'

        node_map={}
        round_map={}
        root=Node(number=-1)
        node_map[-1]=root
        cnt=0
        seed_num=118
        for i in range(seed_num):
            node=Node(number=i,parent=root)
            root.child.append(node)
            node_map[i]=node
        map_node={}
        end_level=[]
        end_node=set()
        cnt=0
        if not os.path.exists(json_path):
            continue
        with open(json_path,'r') as f:
            print(json_path)
            nodes=[json.loads(line) for line in f]
            for i in range(len(nodes)):
                parent_idx = nodes[i]['parent']
                index=nodes[i]['index']

                if nodes[i]['score']:
                    tree_node = Node(number=index, parent=node_map[parent_idx])
                    node_map[index] = tree_node
                else:
                    # print('xxxxxx')
                    cnt+=1
                    tree_node = Node(number='end_{}'.format(index), parent=node_map[parent_idx])
                    node_map[index] = tree_node
                    index = parent_idx
                    while index in node_map.keys() and (node_map[index].level > 0):
                        index = node_map[index].parent.number
                    if index not in node_map.keys():
                        continue
                    if  node_map[index].number in end_node:
                        print('already in {}'.format(node_map[index].number))
                    else:
                        end_node.add(node_map[index].number)
                    if node_map[index].number in all_node:
                        all_node.discard(node_map[index].number)

                node_map[parent_idx].child.append(tree_node)
            print(cnt)
            print(len(end_node))
            print(67-len(end_node))
            counts.append(cnt)
            end_node_lens.append(len(end_node))
print(counts)
print(end_node_lens)
print([67-i for i in end_node_lens])
print([round(1-(67-i)/67,3) for i in end_node_lens])
print(all_node)
print(len(all_node))
# cnt=0
# with open(log_path,'r') as f:
#     lines=f.readlines()
#     # print(len(lines))
#     for line in lines:
#         if 'finish' in line:

#             if len(line.split(' '))<3:
#                 continue
#             cnt += 1
#             index= line.split(' ')[1]
#             index=int(index)
#             node = Node(number='end_{}'.format(index),parent=node_map[index])
#             node_map[index].child.append(node)
#             end_level.append(node_map[index].level+1)

#             while(node_map[index].level>0):
#                 index = node_map[index].parent.number
#             if node_map[index].number in end_node:
#                 print('already in {}'.format(node_map[index].number))
#             else:
#                 end_node.add(node_map[index].number)
# print(cnt)
# # print(sorted(end_level))
# print(len(end_node))
# print(collections.Counter(end_level))






