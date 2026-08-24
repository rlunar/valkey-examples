# Java and Kotlin

Java and Kotlin capsules use the Gradle Wrapper and a declared JVM toolchain.

Required structure:

```text
gradlew
gradlew.bat
gradle/wrapper/
settings.gradle.kts
build.gradle.kts
gradle.lockfile
src/main/
src/test/
```

Requirements:

- commit the Gradle Wrapper and invoke `./gradlew`;
- declare the JVM toolchain in the build;
- use Kotlin build scripts for new capsules;
- enable dependency locking and dependency verification;
- keep production and test sources in the standard Gradle layout;
- configure formatting and static analysis;
- treat compiler warnings according to the capsule's documented policy; and
- run `./gradlew --no-daemon build` in CI.

Do not require a contributor-installed Gradle version.
