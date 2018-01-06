require 'spec_helper'

describe file('/etc/pam.d/login') do
    it {should contain '^@include common-auth' }
    it {should contain '^@include common-account' }
    it {should contain '^@include common-session' }
    it {should contain '^@include common-password' }
end

describe file('/etc/pam.d/common-password') do
  it { should contain '^password \[success=1 default=ignore\] pam_unix.so obscure use_authtok sha512 remember=7 shadow' }
end

describe file('/etc/login.defs') do
  it { should contain '^PASS_MIN_DAYS\s*1' }
end

describe file('/etc/ssh/sshd_config') do
  it {should contain '^PermitEmptyPasswords no'}
  it {should contain '^PubkeyAuthentication yes'}
  it {should contain '^PasswordAuthentication no'}
  it {should contain '^PermitRootLogin no'}
  it {should contain '^RSAAuthentication yes'}
  it {should contain '^HostbasedAuthentication no'}
  it {should contain '^IgnoreRhosts yes'}
  it {should contain '^PrintMotd yes'}
  it {should contain '^PermitUserEnvironment no'}
  it {should contain '^StrictModes yes'}
  it {should contain '^ServerKeyBits 1024'}
  it {should contain '^TCPKeepAlive yes'}
  it {should contain '^LoginGraceTime 120'}
  it {should contain '^MaxStartups 100'}
  it {should contain '^LogLevel INFO'}
  it {should contain '^MaxAuthTries 5'}
  it {should contain '^Protocol 2'}
  it {should contain '^GatewayPorts no'}
  it {should contain '^UsePAM yes'}
  it {should contain '^Ciphers aes128-ctr,aes192-ctr,aes256-ctr'} #OPS092
  it {should contain '^MACs hmac-sha2-256,hmac-sha2-512' } #OPS093
end

describe file('/etc/adduser.conf') do
  it {should contain '^DIR_MODE=700'}
end

describe file('/etc/passwd') do
  it {should_not contain 'password'}
end

files = ['.rhosts','.netrc']
files.each do |file|
  describe file ("~root/#{file}") do
    it {should_not exist}
  end
end

files = ['backup', 'bin', 'boot', 'dev', 'etc', 'home','lib',
  'lib64', 'lost+found', 'media', 'mnt', 'opt', 'proc', 'root',
  'run', 'sbin', 'srv', 'sys', 'usr', 'var']
files.each do |file|
  has_backup_or_other_file = (file != 'backup' || file('/backup/').exists?)
  describe file("/#{file}/"), :if => has_backup_or_other_file do
    it {should be_directory }
    it {should be_mode '[0-7][0-7][0-5]'}
  end
end

files = ['bin', 'include', 'lib', 'local', 'sbin', 'share', 'src']
files.each do |file|
  describe file("/usr/#{file}/") do
    it {should be_directory }
    it {should be_mode '[0-7][0-7][0-5]'}
  end
end

describe file('/etc/security/opasswd') do
  it {should exist}
  it {should be_mode 600}
end

describe file('/etc/shadow') do
  it {should exist}
  it {should be_mode 0000}
end

files = ['backups', 'cache', 'crash', 'lib', 'local',
  'log', 'mail', 'opt', 'spool', 'www']
files.each do |file|
  if File.exist?("/var/#{file}/")
    describe file("/var/#{file}/") do
      it {should be_directory }
      it {should be_mode '[0-2]*[0-7][0-7][0-5]'}
    end
  end
end

describe file('/var/tmp/') do
  it {should be_directory}
  it {should be_mode 1777}
end

describe file('/var/log/faillog') do
  it {should exist}
  it {should be_mode 600}
end

files = ['syslog', 'wtmp', 'auth.log']
files.each do |file|
  describe file ("/var/log/#{file}") do
    it {should exist}
    it {should be_mode '[0-7][0-6][0-5]'}
  end
end

describe file('/tmp/') do
  it {should be_directory}
  it {should be_mode 1777}
end

describe file('/snmpd.conf') do
  it {should_not exist}
end

files = ['inetd.conf', '/xinetd.d/yppasswd']
files.each do |file|
  describe file("/etc/#{file}") do
    it {should_not exist}
  end
end

files = ['/etc/init/', '/var/spool/cron/', '/etc/cron.d/', '/etc/cron.d/drop-expired-keystone-tokens','/etc/cron.d/glance-image-sync', '/etc/cron.d/sysstat',
  '/etc/init.d/', '/etc/rc0.d/', '/etc/rc1.d/', '/etc/rc2.d/','/etc/rc3.d/','/etc/rc4.d/','/etc/rc5.d/','/etc/rc6.d/','/etc/rcS.d/']
files.each do |file|
  if File.exist?("#{file}")
    describe file("#{file}") do
      it {should be_mode '[0-7][0-7][0-5]'}
    end
  end
end

files = ['/', '/usr', '/etc', '/etc/security/opasswd',
	'/etc/shadow', '/var', '/var/tmp', '/var/log',
 	'/var/log/faillog', '/var/log/wtmp', '/tmp']
files.each do |file|
  describe file(file) do
    it { should be_owned_by 'root'}
  end
end

files = ['/var/log/syslog', '/var/log/auth.log']
files.each do |file|
  describe file(file) do
    it { should be_owned_by 'syslog' }
  end
end
