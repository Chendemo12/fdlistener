#!/bin/bash

# 读取control文件内容
content=$(cat ./project/DEBIAN/control)

# 提取Package标签内容
PACKAGE=$(echo "$content" | grep -Po '(?<=Package:)\s*\S+' | tr -d '[:space:]')
# 提取Version标签内容
VERSION=$(echo "$content" | grep -Po '(?<=Version:)\s*\S+' | tr -d '[:space:]')
# 提取Architecture标签内容
ARCH=$(echo "$content" | grep -Po '(?<=Architecture:)\s*\S+' | tr -d '[:space:]')

APP_BIN_DIR="project/opt/apps/bin"
# 待删除的目录名数组
DIRTY_DIRECTORIES=("tmp" "bin")

# 删除目录
delete_directories() {
  # 接受待删除的目录名数组作为参数
  local dirs=("$@")

  # 遍历目录数组
  for dir in "${dirs[@]}"; do
    # 检查目录或文件是否存在
    if [[ -e "$dir" ]]; then
      # 删除目录或文件
      rm -rf "$dir"
    fi
  done
}

# dpkg 打包
make_package() {
  rsync -ah ./project ./tmp/ \
    --exclude=.idea --exclude=.git --exclude=logs \
    --exclude=vendor --exclude=venv

  mkdir ./tmp/project/opt/apps/fdlistener
  rsync -avh ./src ./tmp/project/opt/apps/fdlistener/ --exclude=__pycache__
  rsync -avh ./main.py ./tmp/project/opt/apps/fdlistener/
  rsync -avh ./venv/lib/python3.11/site-packages ./tmp/project/opt/apps/fdlistener/ --exclude=__pycache__


  # 确保拥有可执行权限
  chmod -R 775 ./tmp/project/DEBIAN/*
  chmod -R 775 ./tmp/project/opt/apps/fdlistener/main.py

  mkdir -p ./deb

  # 强制使用gzip打包deb
  # Ubuntu >= 21.04 Supported
  local p=deb/"${PACKAGE}"_"${VERSION}"_"${ARCH}".deb
  dpkg-deb -Zxz --build --root-owner-group tmp/project "$p"

  echo "deb output: $p"
}

echo "**********************************************"
echo "*"
echo "* Package: '$PACKAGE'"
echo "* Version: '$VERSION'"
echo "* Architecture: '$ARCH'"
echo "*"
echo "**********************************************"
echo ""

delete_directories "${DIRTY_DIRECTORIES[@]}"

# 遍历目录数组
for dir in "${DIRTY_DIRECTORIES[@]}"; do
  mkdir -p "$dir"
done

mkdir -p ./tmp/$APP_BIN_DIR/

make_package
delete_directories "${DIRTY_DIRECTORIES[@]}"

exit 0
