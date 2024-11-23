'''
Description: Systemic Financial Crises
version: 1.0
Author: YZP & SYR
Email: yys220124@outlook.com
Tip: Competition code support only, please contact the author
'''
import argparse
import numpy as np
import random

import pandas as pd
import torch

import sys
import os
from pathlib import Path

# 获取项目根目录
root = os.getenv('PROJECT_ROOT')

# 获取项目根目录
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.append(project_root)

def setup_seed(seed):
    torch.manual_seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.enabled = True


setup_seed(415)

from methods import initModelData
from exp.exp_informer import Exp_Informer

parser = argparse.ArgumentParser(description='[Informer] Long Sequences Forecasting')

parser.add_argument('--model', type=str, required=False, default='informer',
                    help='model of experiment, options: [informer, informerstack, informerlight(TBD)]')

parser.add_argument('--data', type=str, required=False, default='ind13-20-day', help='data')
parser.add_argument('--root_path', type=str, default='./data/', help='root path of the data file')
parser.add_argument('--data_path', type=str, default='ind13-20-day.csv', help='data file')
parser.add_argument('--features', type=str, default='MS',
                    help='forecasting task, options:[M, S, MS]; M:multivariate predict multivariate, S:univariate predict univariate, MS:multivariate predict univariate')
parser.add_argument('--target', type=str, default='ind', help='target feature in S or MS task')
parser.add_argument('--freq', type=str, default='d',
                    help='freq for time features encoding, options:[s:secondly, t:minutely, h:hourly, d:daily, b:business days, w:weekly, m:monthly], you can also use more detailed freq like 15min or 3h')
parser.add_argument('--checkpoints', type=str, default='./checkpoints/', help='location of model checkpoints')

parser.add_argument('--seq_len', type=int, default=20, help='input sequence length of Informer encoder')
parser.add_argument('--label_len', type=int, default=15, help='start token length of Informer decoder')
parser.add_argument('--pred_len', type=int, default=1, help='prediction sequence length')
# Informer decoder input: concat[start token series(label_len), zero padding series(pred_len)]

parser.add_argument('--enc_in', type=int, default=7, help='encoder input size')
parser.add_argument('--dec_in', type=int, default=7, help='decoder input size')
parser.add_argument('--c_out', type=int, default=7, help='output size')
parser.add_argument('--d_model', type=int, default=512, help='dimension of model')  # 原来是512                需要调优
parser.add_argument('--n_heads', type=int, default=16, help='num of heads')  # 原来8
parser.add_argument('--e_layers', type=int, default=3, help='num of encoder layers')  # 原来是2                需要调优
parser.add_argument('--d_layers', type=int, default=2, help='num of decoder layers')  #
parser.add_argument('--s_layers', type=str, default='3,2,1', help='num of stack encoder layers')
parser.add_argument('--d_ff', type=int, default=2048, help='dimension of fcn')  # 原来是2048                    需要调优
parser.add_argument('--factor', type=int, default=5, help='probsparse attn factor')
parser.add_argument('--padding', type=int, default=0, help='padding type')
parser.add_argument('--distil', action='store_false',
                    help='whether to use distilling in encoder, using this argument means not using distilling',
                    default=False)  # 原来是True
parser.add_argument('--dropout', type=float, default=0.05, help='dropout')  # 0.05
parser.add_argument('--attn', type=str, default='prob', help='attention used in encoder, options:[prob, full]')
parser.add_argument('--embed', type=str, default='timeF',
                    help='time features encoding, options:[timeF, fixed, learned]')
parser.add_argument('--activation', type=str, default='gelu', help='activation')
parser.add_argument('--output_attention', action='store_true', help='whether to output attention in ecoder')
parser.add_argument('--do_predict', action='store_true', help='whether to predict unseen future data')
parser.add_argument('--mix', action='store_false', help='use mix attention in generative decoder', default=True)
parser.add_argument('--cols', type=str, nargs='+', help='certain cols from the data files as the input features')
parser.add_argument('--num_workers', type=int, default=0, help='data loader num workers')
parser.add_argument('--itr', type=int, default=2, help='experiments times')
parser.add_argument('--train_epochs', type=int, default=16, help='train epochs')  # 改
parser.add_argument('--batch_size', type=int, default=32, help='batch size of train input data')  # 改
parser.add_argument('--patience', type=int, default=6, help='early stopping patience')  # 改
parser.add_argument('--learning_rate', type=float, default=1e-4, help='optimizer learning rate')  # 0.0001
parser.add_argument('--des0', type=str, default='test', help='exp description')  # description
parser.add_argument('--des1', type=str, default='protr', help='exp description')  # description
parser.add_argument('--des2', type=str, default='prov', help='exp description')  # description
parser.add_argument('--des3', type=str, default='prote', help='exp description')  # description
parser.add_argument('--des4', type=str, default='prof', help='exp description')  # description
parser.add_argument('--loss', type=str, default='mse', help='loss function')
parser.add_argument('--lradj', type=str, default='type1', help='adjust learning rate')
parser.add_argument('--use_amp', action='store_true', help='use automatic mixed precision training', default=False)
parser.add_argument('--inverse', action='store_true', help='inverse output data', default=False)

parser.add_argument('--use_gpu', type=bool, default=True, help='use gpu')
parser.add_argument('--gpu', type=int, default=0, help='gpu')
parser.add_argument('--use_multi_gpu', action='store_true', help='use multiple gpus', default=False)
parser.add_argument('--devices', type=str, default='0,1,2,3', help='device ids of multile gpus')

args = parser.parse_args()

args.use_gpu = True if torch.cuda.is_available() and args.use_gpu else False

if args.use_gpu and args.use_multi_gpu:
    args.devices = args.devices.replace(' ', '')
    device_ids = args.devices.split(',')
    args.device_ids = [int(id_) for id_ in device_ids]
    args.gpu = args.device_ids[0]

data_parser = {
    'ETTh1': {'data': 'ETTh1.csv', 'T': 'OT', 'M': [7, 7, 7], 'S': [1, 1, 1], 'MS': [7, 7, 1]},
    'WTH': {'data': 'WTH.csv', 'T': 'WetBulbCelsius', 'M': [12, 12, 12], 'S': [1, 1, 1], 'MS': [12, 12, 1]},
    'DWT13-20': {'data': 'DWT13-20.csv', 'T': 'ind', 'M': [10, 10, 10], 'S': [1, 1, 1], 'MS': [10, 10, 1]},
    'ind13-20-day':{'data': 'ind13-20-day.csv', 'T': 'ind', 'M': [10, 10, 10], 'S': [1, 1, 1], 'MS': [10, 10, 1]},
}

if args.data in data_parser.keys():
    data_info = data_parser[args.data]
    args.data_path = data_info['data']
    args.target = data_info['T']
    args.enc_in, args.dec_in, args.c_out = data_info[args.features]

args.s_layers = [int(s_l) for s_l in args.s_layers.replace(' ', '').split(',')]
args.detail_freq = args.freq
args.freq = args.freq[-1:]

# print('Args in experiment:')
# print(args)

Exp = Exp_Informer

def train():
    for ii in range(args.itr):
        # setting record of experiments
        setting = ('{}_{}_ft{}_sl{}_ll{}_pl{}_dm{}_nh{}_el{}_dl{}_df{}_at{}_fc{}_eb{}_dt{}_mx{}_{}_{}'
                   .format(args.model, args.data, args.features, args.seq_len, args.label_len,
                           args.pred_len,args.d_model,args.n_heads,args.e_layers,args.d_layers,
                           args.d_ff,args.attn,args.factor,args.embed,args.distil,args.mix,args.des0,ii))
        settingtr = ('{}_{}_ft{}_sl{}_ll{}_pl{}_dm{}_nh{}_el{}_dl{}_df{}_at{}_fc{}_eb{}_dt{}_mx{}_{}_{}'
                    .format(args.model, args.data, args.features, args.seq_len, args.label_len,
                            args.pred_len, args.d_model, args.n_heads, args.e_layers, args.d_layers,
                            args.d_ff, args.attn, args.factor, args.embed, args.distil, args.mix, args.des1, ii))
        settingv = ('{}_{}_ft{}_sl{}_ll{}_pl{}_dm{}_nh{}_el{}_dl{}_df{}_at{}_fc{}_eb{}_dt{}_mx{}_{}_{}'
                    .format(args.model, args.data, args.features, args.seq_len, args.label_len,
                            args.pred_len, args.d_model, args.n_heads, args.e_layers, args.d_layers,
                            args.d_ff, args.attn, args.factor, args.embed, args.distil, args.mix, args.des2, ii))
        settingte = ('{}_{}_ft{}_sl{}_ll{}_pl{}_dm{}_nh{}_el{}_dl{}_df{}_at{}_fc{}_eb{}_dt{}_mx{}_{}_{}'
                    .format(args.model, args.data, args.features, args.seq_len, args.label_len,
                            args.pred_len, args.d_model, args.n_heads, args.e_layers, args.d_layers,
                            args.d_ff, args.attn, args.factor, args.embed, args.distil, args.mix, args.des3, ii))
        settingf = ('{}_{}_ft{}_sl{}_ll{}_pl{}_dm{}_nh{}_el{}_dl{}_df{}_at{}_fc{}_eb{}_dt{}_mx{}_{}_{}'
                    .format(args.model, args.data, args.features, args.seq_len, args.label_len,
                            args.pred_len, args.d_model, args.n_heads, args.e_layers, args.d_layers,
                            args.d_ff, args.attn, args.factor, args.embed, args.distil, args.mix, args.des4, ii))
        setting0 = ('{}_{}_ft{}_sl{}_ll{}_pl{}_dm{}_nh{}_el{}_dl{}_df{}_at{}_fc{}_eb{}_dt{}_mx{}_{}_{}'
                    .format(args.model, args.data, args.features, args.seq_len, args.label_len,
                            args.pred_len, args.d_model, args.n_heads, args.e_layers, args.d_layers,
                            args.d_ff, args.attn, args.factor, args.embed, args.distil, args.mix, args.des0, ii))

        exp = Exp(args)  # set experiments
        print('>>>>>>>start training : {}>>>>>>>>>>>>>>>>>>>>>>>>>>'.format(setting))
        exp.train(setting)
        if ii == 1:
            print('>>>>>>> pretesting : {}<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<'.format(setting0))
            exp.pretest(setting0)

        print('>>>>>>> protring : {}<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<'.format(settingtr))
        exp.protr(settingtr)
        print('>>>>>>> proving : {}<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<'.format(settingv))
        exp.prov(settingv)
        print('>>>>>>>testing  : {}<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<'.format(settingte))
        exp.test(settingte)
        print('>>>>>>> profing : {}<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<'.format(settingf))
        exp.prof(settingf)

        torch.cuda.empty_cache()

def train_informer(config):
    initModelData(config)
    cols = df.columns.tolist()[1:]
    name = config['file_info']['name']
    args.root_path = os.path.normpath(f"{root}/opt/{name}/")
    args.data_path = name + '.csv'
    args.target = 'ind'
    args.data = name
    args.train_epochs = config['model_config']['totalEpoch']
    args.batch_size = config['model_config']['batchSize']
    args.gpu = config['model_config']['gpu']
    args.enc_in = len(cols)
    args.dec_in = len(cols)

    print('Args in experiment:')
    print(args)

    try:
        train()
        return True
    except Exception as e:
        print(e)
        return False