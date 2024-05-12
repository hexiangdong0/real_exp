#!/usr/bin/env python
# @lint-avoid-python-3-compatibility-imports
#
# tcprtt    Summarize TCP RTT as a histogram. For Linux, uses BCC, eBPF.
#
# USAGE: tcprtt [-h] [-T] [-D] [-m] [-i INTERVAL] [-d DURATION]
#           [-p LPORT] [-P RPORT] [-a LADDR] [-A RADDR] [-b] [-B] [-e]
#           [-4 | -6]
#
# Copyright (c) 2020 zhenwei pi
# Licensed under the Apache License, Version 2.0 (the "License")
#
# 23-AUG-2020  zhenwei pi  Created this.

from __future__ import print_function
from bcc import BPF
from time import sleep, strftime
from socket import inet_ntop, inet_pton, AF_INET, AF_INET6
import socket, struct
import argparse
import ctypes
import time

# define BPF program
bpf_text = """
#include <uapi/linux/ptrace.h>
#include <linux/tcp.h>
#include <net/sock.h>
#include <net/inet_sock.h>
#include <bcc/proto.h>

struct data_t {
    u64 ts;
    u32 saddr;
    u32 daddr;
    u32 srtt;
    u32 delivered;
    u32 cwnd;
};

struct ip_pair_t {
    u32 saddr;
    u32 daddr;
};

// 创建一个性能事件输出
BPF_PERF_OUTPUT(events);

// 创建一个哈希表来存储每个IP对的计数
BPF_HASH(ip_count, struct ip_pair_t, u64);

int trace_tcp_rcv(struct pt_regs *ctx, struct sock *sk, struct sk_buff *skb)
{
    struct tcp_sock *ts = (struct tcp_sock *)sk;
    const struct inet_sock *inet = (struct inet_sock *)sk;
    struct data_t data = {};
    struct ip_pair_t ip_pair = {};
    u64 zero = 0, *count;

    // 读取IP地址和端口
    bpf_probe_read_kernel(&ip_pair.saddr, sizeof(ip_pair.saddr), (void *)&inet->inet_saddr);
    bpf_probe_read_kernel(&ip_pair.daddr, sizeof(ip_pair.daddr), (void *)&inet->inet_daddr);

    // 对IP地址进行网络字节序转换
    ip_pair.saddr = ntohl(ip_pair.saddr);
    ip_pair.daddr = ntohl(ip_pair.daddr);

    // 获取这个IP对的调用计数
    count = ip_count.lookup_or_init(&ip_pair, &zero);

    // 每次调用都递增计数
    (*count)++;
    
    // 每10次调用执行
    if (*count >= 5) {
        // 重置计数
        *count = 0;

        // 填充数据并提交
        data.ts = bpf_ktime_get_ns();
        data.srtt = ts->srtt_us >> 3;
        data.delivered = ts->delivered;
        data.saddr = ip_pair.saddr;
        data.daddr = ip_pair.daddr;
        data.cwnd = ts->snd_cwnd;
        events.perf_submit(ctx, &data, sizeof(data));
    }

    return 0;
}

"""

log_data = []

record = [0]

def print_event(cpu, data, size):
    event = b["events"].event(data)
    if event.daddr == 0x0a000302 or event.daddr == 0x0a000402:
        log_data.append((event.ts, event.daddr, event.srtt, event.cwnd))


import os
import signal
import pickle


# load BPF program
b = BPF(text=bpf_text)
b.attach_kprobe(event="tcp_rcv_established", fn_name="trace_tcp_rcv")

b["events"].open_perf_buffer(print_event)


def signal_handler(sig, frame):
    print((log_data[-1][0] - log_data[0][0]) / 1e9)
    with open('log.pkl', 'wb') as f:
        pickle.dump(log_data, f)
    print('saved')

signal.signal(signal.SIGINT, signal_handler)


while True:
    b.perf_buffer_poll()


