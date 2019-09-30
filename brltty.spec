%define api_ver 0.6.7

%{!?tcl_version: %global tcl_version %(echo 'puts $tcl_version' | tclsh)}
%{!?tcl_sitearch: %global tcl_sitearch %{_prefix}/%{_lib}/tcl%{tcl_version}}


Name:      brltty
Version:   5.6
Release:   29
Summary:   Braille display driver for Linux/Unix
License:   LGPLv2+
URL:       http://brltty.app/
Source0:   http://brltty.app/archive/%{name}-%{version}.tar.xz

Source1:   brltty.service

#patch0~2 from fedora
Patch0:    brltty-loadLibrary.patch
Patch1:    brltty-5.0-libspeechd.patch
Patch2:    0001-Add-support-for-eSpeak-NG.patch
#patch3~4 from upstream
Patch3:    brltty-5.6-libs-add-ldflags.patch
Patch4:    brltty-5.6-libs-add-ldflags2.patch


BuildRequires: byacc glibc-kernheaders bluez-libs-devel systemd gettext at-spi2-core-devel alsa-lib-devel
BuildRequires: python3-devel autoconf espeak-ng-devel speech-dispatcher-devel


Requires(pre): glibc-common, shadow-utils
Requires(post): coreutils systemd coreutils, util-linux
Requires(preun): systemd
Requires(postun): systemd


Provides:  brlapi
Obsoletes: brlapi

Obsoletes: brltty-espeak <= 5.6-5


%description
BRLTTY is a background process (daemon) which provides
access to the Linux/Unix console (when in text mode)
for a blind person using a refreshable braille display.
It drives the braille display and provides complete
screen review functionality.

%package devel
Summary: Headers, static archive, and documentation for Brltty
Requires: %{name} = %{version}-%{release}

Provides: brlapi-devel = %{api_ver}-%{release}
Obsoletes: brlapi-devel = %{api_ver}-%{release}

%description devel
This package provides the header files, static archive, shared object
linker reference, and reference documentation for Brltty (the
Application Programming Interface to BRLTTY).

%package docs
Summary: Documentation for BRLTTY

%description docs
This package provides the documentation for BRLTTY.


%package -n tcl-%{name}
Requires:      %{name} = %{version}-%{release}
BuildRequires: tcl-devel
Summary: Tcl bpi for brltty
%description -n tcl-brltty
This package provides the Tcl api for Brltty.


%package -n python3-%{name}
%{?python_provide:%python_provide python3-%{name}}
Requires:      %{name} = %{version}-%{release}
BuildRequires: python3-Cython python3-devel
Obsoletes:     python2-%{name} python-%{name}
Summary: Python 3 api for Brltty
%description -n python3-%{name}
This package provides the Python 3 api for Brltty.

%package -n brltty-java
Requires:      %{name} = %{version}-%{release}
BuildRequires: jpackage-utils java-devel
Summary: Java api for Brltty
%description -n brltty-java
This package provides the Java api for Brltty.


%package -n ocaml-brlapi
Requires:      %{name} = %{version}-%{release}
BuildRequires: ocaml
Summary: OCaml api for Brltty
%description -n ocaml-brlapi
This package provides the OCaml api for Brltty.

%package xw
Summary: XWindow driver for BRLTTY
License: LGPLv2+
BuildRequires: libSM-devel libICE-devel libX11-devel libXaw-devel libXext-devel libXt-devel libXtst-devel
Requires: %{name} = %{version}-%{release}
Requires: xorg-x11-fonts-misc, ucs-miscfixed-fonts
%description xw
The XWindow driver for BRLTTY.

%package at-spi2
Summary: AtSpi2 driver for BRLTTY
License: LGPLv2+
Requires: %{name} = %{version}-%{release}
%description at-spi2
The AtSpi2 driver for BRLTTY.



%prep
%autosetup -n %{name}-%{version} -p1


%build
export PYTHONCOERCECLOCALE=0
PYTHONS=
./autogen

%configure --disable-relocatable-install --with-install-root="${RPM_BUILD_ROOT}" --disable-stripping --without-curses \
           --without-espeak JAVA_JAR_DIR=%{_jnidir} JAVA_JNI_DIR=%{_libdir}/brltty JAVA_JNI=yes \
           CYTHON=%{_bindir}/cython PYTHON=%{__python3}
%make_build


find . \( -path ./doc -o -path ./Documents \) -prune -o \
  \( -name 'README*' -o -name '*.txt' -o -name '*.html' -o \
     -name '*.sgml' -o -name '*.patch' -o \
     \( -path './Bootdisks/*' -type f -perm /ugo=x \) \) -print |
while read file; do
   mkdir -p ./doc/${file%/*} && cp -rp $file ./doc/$file || exit 1
done

%install
mkdir -p $RPM_BUILD_ROOT%{_libdir}/ocaml/stublibs
%make_install JAVA_JAR_DIR=%{_jnidir} JAVA_JNI_DIR=%{_libdir}/brltty JAVA_JNI=yes
install -m 0644 Documents/brltty.conf ${RPM_BUILD_ROOT}%{_sysconfdir}
install -D -p -m 0644 %{SOURCE1} $RPM_BUILD_ROOT%{_unitdir}/brltty.service
chmod 755 ${RPM_BUILD_ROOT}%{_bindir}/brltty-config

rm -rf $RPM_BUILD_ROOT/%{_libdir}/libbrlapi.a

%find_lang %{name}
cp -p %{name}.lang ../

/usr/bin/2to3 -wn ${RPM_BUILD_ROOT}/etc/brltty/Contraction/latex-access.ctb
sed -i 's|/usr/bin/python|/usr/bin/python3|g' ${RPM_BUILD_ROOT}/etc/brltty/Contraction/latex-access.ctb

%check

%pre
if ! getent group brlapi > /dev/null ; then
    groupadd -r brlapi > /dev/null
fi


%preun
%systemd_preun brltty.service

%post
if [ ! -e %{_sysconfdir}/brlapi.key ]; then
  mcookie > %{_sysconfdir}/brlapi.key
  chgrp brlapi %{_sysconfdir}/brlapi.key
  chmod 0640 %{_sysconfdir}/brlapi.key
fi
/sbin/ldconfig
%systemd_post brltty.service


%postun
/sbin/ldconfig
%systemd_postun_with_restart brltty.service


%files -f %{name}.lang
%defattr(-,root,root)
%license LICENSE-*

%config(noreplace) %{_sysconfdir}/brltty.conf


%{_bindir}/brltty
%{_bindir}/brltty-*
%{_bindir}/vstp
%{_bindir}/eutp
%{_bindir}/xbrlapi

%{_libdir}/brltty/
%{_libdir}/libbrlapi.so.*
%exclude %{_libdir}/brltty/libbrlttyssd.so
%exclude %{_libdir}/brltty/libbrlttybxw.so
%exclude %{_libdir}/brltty/libbrlttyxa2.so
%exclude %{_libdir}/brltty/libbrlttysen.so
%exclude %{_libdir}/brltty/libbrlapi_java.so

%{_sysconfdir}/brltty/
%{_sysconfdir}/X11/Xsession.d/60xbrlapi

%{_datadir}/polkit-1/actions/org.a11y.brlapi.policy
%exclude %{_datadir}/gdm/greeter/autostart/xbrlapi.desktop

%{_unitdir}/brltty.service


%files  devel
%{_libdir}/libbrlapi.so
%{_includedir}/brltty
%{_includedir}/brlapi*.h


%files docs
%defattr(644,root,root)
%doc doc/*
#%doc Drivers/Speech/SpeechDispatcher/README
#%doc Drivers/Braille/XWindow/README
%doc Documents/*
%doc %{_mandir}/man[15]/brltty.*
%doc %{_mandir}/man1/xbrlapi.*
%doc %{_mandir}/man1/vstp.*
%doc %{_mandir}/man1/eutp.*
%doc %{_mandir}/man3/brlapi_*.3*


%files -n tcl-%{name}
%{tcl_sitearch}/brlapi-%{api_ver}

%files -n python3-%{name}
%{python3_sitearch}/brlapi.cpython-*.so
%{python3_sitearch}/Brlapi-%{api_ver}-*.egg-info


%files -n brltty-java
%{_libdir}/brltty/libbrlapi_java.so
%{_jnidir}/brlapi.jar


%files -n ocaml-brlapi
%{_libdir}/ocaml/brlapi/
%{_libdir}/ocaml/stublibs

%files xw
%doc Drivers/Braille/XWindow/README
%{_libdir}/brltty/libbrlttybxw.so

%files at-spi2
%{_libdir}/brltty/libbrlttyxa2.so


%changelog
* Wed Sep 18 2019 openEuler Buildteam <buildteam@openeuler.org> - 5.6-29
- Type:bugfix
- Id:NA
- SUG:NA
- DESC: Adjust the position of ldconfig in the post stage

* Thu Sep 12 2019 hufeng <solar.hu@huawei.com> - 5.6-28
- Init  spec
