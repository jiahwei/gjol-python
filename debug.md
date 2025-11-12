# 各种奇怪的BUG

## ERRO[0000] Refreshing container : error acquiring lock for container : file exists

使用非root用户部署podman镜像，在退出SSH之后，再次登录时，podman ps会出现上述错误。

```bash
[deploy@VM-16-9-opencloudos ~]$ podman ps
ERRO[0000] Refreshing container 3f00047d0b2f289cefbaa56e7ce9d31337a1180488df8602eafbc5793c0c8ec8: acquiring lock 1 for container 3f00047d0b2f289cefbaa56e7ce9d31337a1180488df8602eafbc5793c0c8ec8: file exists
ERRO[0000] Refreshing container 67e26adc4eded6b17fe98b29829005ef34cc98b4d4b7cc53f94260494242f388: acquiring lock 0 for container 67e26adc4eded6b17fe98b29829005ef34cc98b4d4b7cc53f94260494242f388: file exists
CONTAINER ID  IMAGE       COMMAND     CREATED     STATUS      PORTS       NAMES
```

解决方案：

[参考Github的讨论](https://github.com/containers/podman/issues/16784)，尝试给deploy用户启用 linger 特性。

```bash
[deploy@VM-16-9-opencloudos ~]$ loginctl user-status | grep -m1 Linger
          Linger: no
# 使用root用户启用linger特性，或是deploy用户有sudo权限
[root@VM-16-9-opencloudos ~]# loginctl enable-linger deploy
# 检查deploy用户是否启用了linger特性
[deploy@VM-16-9-opencloudos ~]$ loginctl user-status | grep -m1 Linger
          Linger: yes
```

重启镜像

```bash
podman restart -a

# 报错就删除重新启动
podman rm -f gjoldb-server gjol-nuxt
```

目前看起来是好的，GitHub上的讨论也提到了**此解决方法在系统重启后将不再有效**，或许需要重新启用 linger 特性。

嗨，反正服务器也一年也重启不了一次，就这样吧
