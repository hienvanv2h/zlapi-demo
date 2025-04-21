# escape=`
FROM mcr.microsoft.com/windows/servercore:20H2

# Tạo thư mục làm việc
WORKDIR C:/app

RUN powershell.exe -Command `
    $ErrorActionPreference = 'Stop'; `
    wget https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe -OutFile c:\python-3.11.4.exe ; `
    Start-Process c:\python-3.11.4.exe -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1' -Wait ; `
    Remove-Item c:\python-3.11.4.exe -Force

    # Xác minh đã cài Python thành công
RUN python --version

# Sao chép mã nguồn project
COPY . .

# Cài pip nếu cần (thường đã có)
RUN python -m ensurepip --upgrade && `
    python -m pip install --upgrade pip && `
    python -m pip install -r requirements.txt

# Thiết lập chạy ứng dụng
CMD ["python", "main.py"]