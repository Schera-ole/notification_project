FROM python:3.11
RUN groupadd -r praktikum && useradd -r -g praktikum praktikum \
     && mkdir /home/praktikum \
     && chown praktikum:praktikum /home/praktikum
ENV PATH="${PATH}:/home/praktikum/.local/bin"
WORKDIR /app
RUN chown -R praktikum:praktikum /app
COPY requirements.txt requirements.txt
RUN  pip install --upgrade pip \
     && pip install --no-cache-dir -r requirements.txt &&  pip install  pydantic-settings
COPY --chown=praktikum ./src ./
USER praktikum
EXPOSE 9000