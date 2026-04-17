# 取证工具速查

<!-- 目录 -->
<!-- 1. binwalk -->
<!-- 2. steghide -->
<!-- 3. foremost -->
<!-- 4. exiftool -->
<!-- 5. zsteg -->
<!-- 6. pngcheck -->
<!-- 7. 常用取证技术 -->

---

## 1. binwalk

binwalk 是固件分析和提取的利器,常用于查找嵌入文件。

### 安装

```bash
# macOS
brew install binwalk

# Ubuntu/Debian
sudo apt install binwalk

# 从源码
git clone https://github.com/ReFirmLabs/binwalk
cd binwalk
python setup.py install
```

### 基本使用

```bash
# 扫描文件
binwalk firmware.bin

# 显示详细信息 (-v)
binwalk -v firmware.bin

# 递归扫描 (-e, --extract)
binwalk -e firmware.bin

# 递归提取 (-e, --extract, -r 清理无效文件)
binwalk -e -r firmware.bin

# 显示字符串分析 (-A)
binwalk -A binary

# 签名扫描 (-S)
binwalk -S binary

# 原始字节搜索 (-B, --magic)
binwalk -B binary

# 指定起始位置 (-m, --start)
binwalk -m 0x1000 firmware.bin

# 指定结束位置 (-l, --length)
binwalk -l 0x1000 firmware.bin
```

### 常用选项

```bash
# -e, --extract     自动提取已知签名
# -eM, --megapify   递归提取提取出的文件
# -r, --rm          清理无效的零大小文件
# -d, --dont-scrub  不提取空签名
# -j, --size        每个提取文件的大小限制
# -y, --include     只搜索指定签名
# -x, --exclude     排除指定签名
```

### 签名过滤

```bash
# 只搜索 ZIP
binwalk -y "zip" firmware.bin

# 排除 JPG
binwalk -x "jpg" firmware.bin

# 搜索多个
binwalk -y "zip;png;jpg" firmware.bin
```

### 提取后的操作

```bash
# 查看提取的目录
ls -la _firmware.bin.extracted/

# 使用 binwalk 查找目录中的内容
binwalk -e -M _firmware.bin.extracted/
```

### Python API

```python
import binwalk

# 扫描
for module in binwalk.scan('firmware.bin', signature=True, quiet=True):
    print(f"Module: {module.name}")
    for result in module.results:
        print(f"  {result.offset:x} - {result.description}")

# 提取
binwalk.extract('firmware.bin', extraction_directory='./output')
```

---

## 2. steghide

steghide 用于隐藏和提取数据到图片或音频文件中。

### 安装

```bash
# macOS
brew install steghide

# Ubuntu/Debian
sudo apt install steghide
```

### 基本使用

```bash
# 提取隐藏数据
steghide extract -sf image.jpg

# 指定输出文件
steghide extract -sf image.jpg -xf output.txt

# 嵌入数据
steghide embed -cf image.jpg -ef secret.txt

# 指定嵌入文件
steghide embed -cf image.jpg -ef secret.txt -p "password"

# 查看嵌入信息
steghide info image.jpg
```

### 常用选项

| 选项 | 说明 |
|------|------|
| `-cf, --coverfile` | 载体文件 |
| `-ef, --embedfile` | 要嵌入的文件 |
| `-sf, --stegofile` | 包含嵌入数据的文件 |
| `-xf, --extractfile` | 提取后的文件名 |
| `-p, --passphrase` | 密码 |
| `-e, --encryption` | 加密算法 |
| `-z, --compress` | 压缩级别 (1-9) |

### 暴力破解

```bash
# 使用 stegcracker (需要先安装)
stegcracker image.jpg wordlist.txt

# 或使用 steghide 内置
steghide --extract -sf image.jpg -p "" 2>/dev/null
```

---

## 3. foremost

foremost 是文件恢复工具,根据文件头签名恢复文件。

### 安装

```bash
# macOS
brew install foremost

# Ubuntu/Debian
sudo apt install foremost
```

### 基本使用

```bash
# 基本恢复
foremost -i disk.img

# 指定输出目录
foremost -i disk.img -o output/

# 查看支持的类型
foremost -h

# 指定文件类型
foremost -t jpg,png,gif -i disk.img

# 全部类型
foremost -t all -i disk.img

# 详细模式
foremost -v -i disk.img

# 快速模式 (只搜索文件头)
foremost -q -i disk.img

# 保守模式 (不覆盖已提取的文件)
foremost -c -i disk.img
```

### 配置文件

```bash
# 查看默认配置
cat /etc/foremost.conf
# 或
/usr/local/etc/foremost.conf

# 自定义配置
foremost -c my.conf -i disk.img
```

### foremost.conf 格式

```conf
# 格式: 扩展名 文件头 "尾部" 最大大小
jpg     y       \xff\xd8    \xff\xd9    200000
png     y       \x89\x50\x4e\x47    \x49\x45\x4e\x44    100000
gif     y       \x47\x49\x46\x38    \x00\x3b         100000
zip     y       \x50\x4b\x03\x04    \x50\x4b\x05\x06    200000
pdf     y       \x25\x50\x44\x46    \x25\x45\x4f\x46    5000000
```

---

## 4. exiftool

exiftool 是读取和写入 EXIF 信息的工具。

### 安装

```bash
# macOS
brew install exiftool

# Ubuntu/Debian
sudo apt install libimage-exiftool-perl
```

### 基本使用

```bash
# 读取所有 EXIF 信息
exiftool image.jpg

# 只显示特定信息
exiftool -Make image.jpg          # 相机厂商
exiftool -Model image.jpg         # 相机型号
exiftool -DateTimeOriginal image.jpg  # 拍摄时间
exiftool -GPSLatitude image.jpg   # GPS 纬度
exiftool -GPSLongitude image.jpg  # GPS 经度

# 显示简短信息
exiftool -s image.jpg

# 显示所有可用标签
exiftool -listx image.jpg

# 写入 EXIF
exiftool -Artist="Name" image.jpg

# 复制 EXIF
exiftool -TagsFromFile src.jpg dst.jpg

# 删除所有 EXIF
exiftool -All= image.jpg

# 调整时间
exiftool -DateTimeOriginal="2024:01:01 12:00:00" image.jpg

# 删除特定标签
exiftool -GPSLatitude= image.jpg
```

### 常用标签

| 标签 | 说明 |
|------|------|
| `-Make` | 设备厂商 |
| `-Model` | 设备型号 |
| `-DateTimeOriginal` | 原始拍摄时间 |
| `-CreateDate` | 创建时间 |
| `-GPSLatitude` | GPS 纬度 |
| `-GPSLongitude` | GPS 经度 |
| `-ImageWidth` | 图像宽度 |
| `-ImageHeight` | 图像高度 |
| `-Software` | 软件 |
| `-Artist` | 作者 |
| `-Copyright` | 版权 |
| `-ExposureTime` | 曝光时间 |
| `-FNumber` | 光圈 |
| `-ISO` | ISO |
| `-FocalLength` | 焦距 |

### 批量操作

```bash
# 批量读取目录
exiftool directory/

# 递归处理
exiftool -r directory/

# 批量修改
exiftool "-DateTimeOriginal+=0:0:0 1:0:0" *.jpg

# 提取缩略图
exiftool -b -ThumbnailImage image.jpg > thumb.jpg

# 提取预览图
exiftool -b -PreviewImage image.jpg > preview.jpg
```

---

## 5. zsteg

zsteg 是专门用于 PNG 和 BMP 图片的 LSB 隐写分析工具。

### 安装

```bash
# macOS
brew install zsteg

# 从源码
gem install zsteg
```

### 基本使用

```bash
# 分析图片
zsteg image.png

# 显示所有尝试
zsteg -v image.png

# 提取 LSB 数据
zsteg -E "b1,lsb,xy" image.png > output

# 指定通道
zsteg -E "b2,lsb,xy" image.png

# 显示帮助
zsteg --help
```

### 通道选择器

```
b1      第一字节平面 (最低位)
b2      第二字节平面
b3,b4   更高位平面

lsb     最低有效位 (默认)
msb     最高有效位

xy      逐行扫描 (默认)
x,y     逐列扫描
z       zigzag 扫描

all     所有通道组合
```

### 常用命令

```bash
# 检测 LSB 隐写
zsteg image.png

# 检测 LSB with z-ordering
zsteg -a image.png

# 提取第一平面的 LSB
zsteg -E "b1,lsb,xy" image.png > extracted.bin

# 提取并查看
zsteg -E "b1,lsb,xy" image.png | strings

# 检测特定文件类型
zsteg -E "b1,lsb,xy,ext" image.png
```

### 高级用法

```bash
# 尝试所有组合
zsteg -a image.png

# 检测 RSA/DSA 私钥
zsteg image.png | grep -i "rsa\|dsa\|begin"

# 检测 URLs
zsteg image.png | grep -E "http://|https://"

# 检测 Base64
zsteg image.png | grep -E "[A-Za-z0-9+/=]{20,}"
```

---

## 6. pngcheck

pngcheck 用于验证和调试 PNG 图片。

### 安装

```bash
# macOS
brew install pngcheck

# Ubuntu/Debian
sudo apt install pngcheck
```

### 基本使用

```bash
# 验证 PNG
pngcheck image.png

# 详细输出
pngcheck -v image.png

# 更详细
pngcheck -vv image.png

# 提取 tEXt chunks
pngcheck -t image.png

# 显示所有 chunk 信息
pngcheck -c image.png

# 修复 (显示信息)
pngcheck -f image.png
```

### 常见错误

```bash
# CRC 错误 - 图片损坏或修改过
pngcheck image.png
# 输出: image.png:  CRC error in chunk IHDR (computed XXXX, expected YYYY)

# 未完成 - 图片截断
pngcheck image.png
# 输出: image.png:  EOF while reading chunk
```

---

## 7. 常用取证技术

### 图片隐写

```bash
# 1. 检查文件类型
file image.jpg

# 2. 查看 hex dump
xxd image.jpg | head
hexdump -C image.jpg | head

# 3. 查看 strings
strings image.jpg

# 4. 检查 EXIF
exiftool image.jpg

# 5. LSB 分析
zsteg image.png        # PNG/BMP
stegsolve image.jpg    # 需要 Java

# 6. 隐藏文件检测
binwalk image.jpg

# 7. 提取隐藏数据
foremost -t all -i image.jpg
```

### 流量分析

```bash
# 查看 pcap 文件
tcpdump -r capture.pcap

# 过滤
tcpdump -r capture.pcap "port 80"

# 使用 wireshark/tshark
tshark -r capture.pcap -Y "http" | head

# 导出特定流
tcpflow -r capture.pcap

# 提取 HTTP 对象
chaosreader capture.pcap
```

### 内存取证

```bash
# 内存dump
./LiME/src/lime.ko
insmod lime.ko "path=/tmp/mem.dat format=lime"

# 分析 (Volatility)
volatility -f mem.dat --profile=Win7SP1x64 pslist
volatility -f mem.dat --profile=Win7SP1x64 psscan
volatility -f mem.dat --profile=Win7SP1x64 netscan
volatility -f mem.dat --profile=Win7SP1x64 cmdline
```

### 磁盘取证

```bash
# 挂载
mount -o loop disk.img /mnt

# 查看分区
fdisk -l disk.img

# 文件恢复
foremost -i disk.img
photorec disk.img

# 查看历史记录
mactime -b timeline.body > timeline.txt

# 查看已删除文件
fls -r -d disk.img
```

### 文件分析

```bash
# 文件类型
file image.jpg

# 熵值分析 (高熵 = 压缩/加密,低熵 = 普通数据)
binwalk -E image.jpg

# 隐藏检测
icat disk.img 5 | strings

# 查看文件结构
ghex2 image.jpg
bless image.jpg
```

### 常用取证命令

```bash
# 查找关键词
grep -a "password" disk.img
grep -a -i "secret" disk.img

# 查找 URL
grep -aoE "https?://[^ ]+" disk.img

# 查找 IP
grep -aoE "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" disk.img

# 查找文件头
for f in $(strings disk.img | grep -E "^[A-Za-z0-9+/=]{20,}$"); do
    echo "$f" | base64 -d 2>/dev/null | file -
done

# 提取特定类型文件
binwalk -y "jpeg;jpg;png" disk.img
```

---

## 常见隐写类型

### LSB (Least Significant Bit)

最低有效位隐写,将数据藏在像素的最低位
- 工具: zsteg, stegsolve, ImageSteg

### DCT (Discrete Cosine Transform)

JPEG 压缩域隐写
- 工具: jsteg, outguess, stegdetect

### 追加数据

将数据追加到文件末尾
- 检测: `binwalk image.jpg`

### 双图

两张看起来相同的图片,但有细微差别
- 工具: `compare img1.png img2.png`

### 频域

将数据隐藏在频域中
- 工具: stegsolve, openstego

---

##取证检查清单

1. **文件分析**
   - [ ] `file` - 确定真实文件类型
   - [ ] `xxd` / `hexdump` - 查看原始内容
   - [ ] `strings` - 查看可打印字符串
   - [ ] `binwalk` - 查找嵌入数据

2. **图片分析**
   - [ ] `exiftool` - 查看 EXIF
   - [ ] `zsteg` - LSB 分析
   - [ ] `pngcheck` - PNG 验证
   - [ ] `steghide` - 尝试提取

3. **流量分析**
   - [ ] `tcpdump` - 基础分析
   - [ ] `wireshark` - 详细分析
   - [ ] `tshark` - 命令行分析

4. **内存/磁盘**
   - [ ] `foremost` - 文件恢复
   - [ ] `volatility` - 内存分析
   - [ ] `fls` - 文件系统分析
