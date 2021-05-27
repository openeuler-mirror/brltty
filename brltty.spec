%define api_ver 0.8.0
%define tcl_version tcl8.6
%{!?tcl_sitearch: %global tcl_sitearch %{_prefix}/%{_lib}/%{tcl_version}}

%bcond_with espeak
%bcond_with speech

Name:      brltty
Version:   6.1
Release:   3
Summary:   Braille display driver for Linux/Unix
License:   LGPLv2+
URL:       http://brltty.app/
Source0:   http://brltty.app/archive/%{name}-%{version}.tar.xz

Source1:   brltty.service

Patch0:    brltty-6.1-loadLibrary.patch

%if %{with speech}
Patch1:    brltty-5.0-libspeechd.patch
%endif

BuildRequires: brltty tcl-brltty byacc glibc-kernheaders bluez-libs-devel systemd gettext gdb
BuildRequires: python3-devel autoconf at-spi2-core-devel alsa-lib-devel
BuildRequires: automake

%if %{with espeak}
BuildRequires: espeak-ng-devel
%endif

%if %{with speech}
BuildRequires: speech-dispatcher-devel
%endif


Requires(pre): glibc-common, shadow-utils
Requires(post): coreutils systemd coreutils, util-linux
Requires(preun): systemd
Requires(postun): systemd


Provides:  brlapi
Obsoletes: brlapi

%if %{without espeak}
Obsoletes: brltty-espeak <= 5.6-5
%endif

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
Obsoletes: brlapi-devel < %{api_ver}-%{release}

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
Provides:      python3-brlapi = %{version}-%{release}
Obsoletes:     python3-brlapi < %{version}-%{release}
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
           JAVA_JAR_DIR=%{_jnidir} JAVA_JNI_DIR=%{_libdir}/brltty JAVA_JNI=yes \
           CYTHON=%{_bindir}/cython PYTHON=%{__python3} \
%if %{without espeak}
          --without-espeak
%endif

make VERBOSE=1


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
cp -a %{_libdir}/libbrlapi.so.* %{buildroot}%{_libdir}
cp -a %{_libdir}/tcl8.6/brlapi-* %{buildroot}%{_libdir}/tcl8.6
 
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
%exclude %{_libdir}/brltty/libbrlttybxw.so
%exclude %{_libdir}/brltty/libbrlttyxa2.so
%exclude %{_libdir}/brltty/libbrlapi_java.so

%{_sysconfdir}/brltty/
%{_sysconfdir}/X11/Xsession.d/90xbrlapi

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
%{tcl_sitearch}/brlapi-0.6.7

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
* Thu May 27 2021 lijingyuan <lijingyuan3@huawei.com> - 6.1-3
- Type:bugfix
- Id:NA
- SUG:NA
- DESC:Add the compilation dependency of automake.

* Tue Dec 15 2020 xihaochen <xihaochen@huawei.com> - 6.1-2
- Type:requirement
- Id:NA
- SUG:NA
- DESC:remove sensitive words 

* Thu Jul 23 2020 gaihuiying <gaihuiying1@huawei.com> - 6.1-1
- Type:requirement
- Id:NA
- SUG:NA
- DESC:update brltty version to 6.1

* Wed Mar 18 2020 songnannan <songnannan2@huawei.com> - 5.6-35
- change the path for tcl

* Tue Mar 17 2020 songnannan <songnannan2@huawei.com> - 5.6-34
- add gdb in buildrequires

* Tue Jan 14 2020 openEuler Buildteam <buildteam@openeuler.org> - 5.6-33
- Type:bugfix
- Id:NA
- SUG:NA
- DESC:bugfix about files in build process

* Fri Dec 27 2019 openEuler Buildteam <buildteam@openeuler.org> - 5.6-32
- Type:bugfix
- Id:NA
- SUG:NA
- DESC:fix update problem

* Wed Dec 04 2019 openEuler Buildteam <buildteam@openeuler.org> - 5.6-31
- Type:bugfix
- Id:NA
- SUG:NA
- DESC: add the release

* Wed Oct 30 2019 caomeng <caomeng5@huawei.com> - 5.6-30
- Type:NA
- ID:NA
- SUG:NA
- DESC:add bcondwith espeak and speech

* Wed Sep 18 2019 openEuler Buildteam <buildteam@openeuler.org> - 5.6-29
- Type:bugfix
- Id:NA
- SUG:NA
- DESC: Adjust the position of ldconfig in the post stage

* Thu Sep 12 2019 hufeng <solar.hu@huawei.com> - 5.6-28
- Init  spec
